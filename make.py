#!/usr/bin/env python3
# Copyright (c) 2024 Chris Henning
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
import sys, os, io, re, copy, shutil, traceback
import Diagraphers_Stellaris_Mods.cw_parser_2 as cwp
from pathlib import Path
cwp.workshop_path = os.path.expanduser( os.path.expandvars( "~/stellaris-workshop" ) )
cwp.mod_docs_path = os.path.expanduser( os.path.expandvars( "~/stellaris-mod" ) )
cwp.vanilla_path = os.path.expanduser( os.path.expandvars( "~/stellaris-game" ) )
MOD_NAME = "Better Crime Automation"
VERSION = "2"
SUPPORTED_VERSION = "v3.13.*"
# Balance, Buildings, Diplomacy, Economy, Events, Fixes, Font, Galaxy
# Generation, Gameplay, Graphics, Leaders, Loading Screen, Military, Overhaul,
# Sound, Spaceships, Species, Technologies, Total Conversion, Translation, Utilities
TAGS = [ "Gameplay" ]
# 3 = unlisted, 2 = hidden, 1 = friends, 0 = public
VISIBILITY = 0

from snippets import *

def fail(message, err=None):
  if err:
    traceback.print_tb(err.__traceback__)
  print(f"{message}", file=sys.stderr)
  sys.exit(1)

# Make descriptor.mod
def make_descriptor(path="mod/descriptor.mod"):
  outlines = []
  outlines.append(f"name=\"{MOD_NAME}\"\r\n")
  outlines.append(f"version=\"{VERSION}\"\r\n")
  outlines.append(f"supported_version=\"{SUPPORTED_VERSION}\"\r\n")
  outlines.append("tags={\r\n")
  for tag in TAGS:
    outlines.append(f"\t\"{tag}\"\r\n")
  outlines.append("}\r\n")
  outlines.append("picture=\"thumbnail.png\"\r\n")

  try:
    with open(path, "w") as file:
      file.writelines(outlines)
  except Exception as e:
    fail("Failed writing file", e)

# Make steamcmd.txt
def make_steamcmd():
  if not os.path.exists("steamcmd.txt"):
    shutil.copy("steamcmd-template.txt", "steamcmd.txt")
  steamcmd = []
  with open("steamcmd.txt", "r") as file:
    steamcmd = file.readlines()
  with open("steamcmd.txt", "w") as file:
    for line in steamcmd:
      if '"contentfolder"' in line or '"previewfile"' in line:
        line = line.replace("FULLMODPATH", os.getcwd())
      elif '"title"' in line:
        line = f'\t"title"\t\t"{MOD_NAME}"\n'
      elif '"visibility"' in line:
        line = f'\t"visibility"\t\t"{VISIBILITY}"\n'
      elif '"description"' in line and '"New description."' in line:
        line = ""

      file.write(line)

# Adjust job weights for enforcers to account for crime waves and stability
# infilename: relative to, not including, the vanilla base
# outfilename: just the filename, no path
def process_job(infilename, outfilename):
  outlist = []
  dirname = "mod/" + os.path.dirname( infilename )
  fulloutfile = f"{dirname}/{outfilename}"
  delete_file(fulloutfile)
  # Read in vanilla
  try:
    cw = cwp.fileToCW(f"{cwp.vanilla_path}/{infilename}" )
  except Exception as e:
    fail(f"Failed to parse {infilename}, {e}", e)
  # Process crime automation and add to it
  for ele in cw:
    if ele.name in [ "enforcer", "patrol_drone" ]:
      if not ele.hasAttribute("weight"):
        fail(f"{ele.name} missing weights??")
      wele = ele.getElement("weight")
      modifiers = wele.getElements("modifier")
      # Add a new weight for the crime wave
      wele.subelements.extend(crime_wave[ele.name])
      # Add new weights for enforcer stability
      if ele.name == "enforcer":
        wele.subelements.extend(cwp.stringToCW(enforcer_stability_str))
      # Vanilla enforcers have a drastic reduction in job weight when crime is
      # under 15. Change that. Vanilla patrol drones don't have a reduction for
      # low crime.
      mcount = 0
      for mele in modifiers:
        mcount += 1
        try:
          if mele.hasAttribute("factor") and float(mele.getValue("factor")) > 1.0:
            continue
        except Exception as e:
          fail(f"Error testing factor in {ele.name}, {e}", e)
        if mele.hasAttribute("planet"):
          mpele = mele.getElement("planet")
          if mpele.hasAttribute("planet_crime"):
            mcele = mpele.getElement("planet_crime")
            mcele.value = str(CRIME_WAVE_THRESH)
            mcele.comparison = "<"
 
      # Vanilla has many weight modifiers, do a sanity check
      if mcount < 5:
        fail(f"Suspiciously low weight modifiers ({mcount}) in {ele.name}?")
      # Add the modified top level element to our write list
      outlist.append(ele)
  write_file(outlist, dirname, outfilename)

# Adjust crime planetary automation to take in to account crime waves and
# stability
# infilename: relative to, not including, the vanilla base
# outfilename: just the filename, no path
def process_crime(infilename, outfilename):
  outlist = []
  dirname = "mod/" + os.path.dirname( infilename )
  fulloutfile = f"{dirname}/{outfilename}"
  delete_file(fulloutfile)
  # Read in vanilla
  try:
    cw = cwp.fileToCW(f"{cwp.vanilla_path}/{infilename}" )
  except Exception as e:
    fail(f"Failed to parse {infilename}, {e}", e)
  # Process crime automation and add to it
  for ele in cw:
    if ele.name in [ "automate_crime_management", "automate_crime_management_gestalt" ]:
      # Handle Enforcer job openings
      if not ele.hasAttribute("job_changes"):
        fail(f"{ele.name} missing job_changes??")
      jobele = ele.getElement("job_changes")
      # Add stability conditions to non gestalt only (hunter seeker drones do
      # not improve stability)
      if ele.name == "automate_crime_management":
        # enforcer_reduce block: Vanilla has one 
        if sum(1 for x in jobele.getElements("enforcer_reduce")) != 1:
          fail(f"Unexpected number of enforcer_reduce blocks in {ele.name}, what did vanilla change?")
        redele = jobele.getElement("enforcer_reduce")
        if not redele.hasAttribute("available"):
          fail(f"{ele.name} > enforcer_reduce > available missing")
        redele.getElement("available").subelements.extend( 
                      cwp.stringToCW("planet_stability > @stabilitylevel3 NAND = { has_branch_office = yes branch_office_owner = { is_criminal_syndicate = yes } }")
                      )
        # enforcer_increase block: Vanilla has one 
        if sum(1 for x in jobele.getElements("enforcer_increase")) != 1:
          fail(f"Unexpected number of enforcer_increase blocks in {ele.name}, what did vanilla change?")
        incele = jobele.getElement("enforcer_increase")
        if not incele.hasAttribute("available"):
          fail(f"{ele.name} > enforcer_increase > available missing")
        incavaele = incele.getElement("available")
        existing_inc_ava_str = cwp.CWToString(incavaele.subelements)
        # Assume all vanilla conditions can be OR'd with our stability condition
        incavaele.subelements = cwp.stringToCW(f"OR = {{ {existing_inc_ava_str} planet_stability < @stabilitylevel2 }}")

      # Add another stanza for really bad planets to both gestalt and non
      jobele.subelements.extend(enforcer_increase[ele.name])

      # Handle building Precincts
      if not ele.hasAttribute("buildings"):
        fail(f"{ele.name} missing buildings??")
      buildele = ele.getElement("buildings")
      if not buildele.hasAttribute("precinct"):
        fail(f"{buildele.name} missing precinct??")
      precele = buildele.getElement("precinct")
      if not precele.hasAttribute("available"):
        fail(f"{precele.name} missing available??")
      avaele = precele.getElement("available")
      if not avaele.hasAttribute("planet_crime"):
        fail(f"{avaele.name} missing planet_crime??")
      pcele = avaele.getElement("planet_crime")

      newele = cwp.stringToCW("OR = { }")
      # Combine the vanilla planet_crime check with a new one of our making
      newele[0].subelements.extend([pcele])
      newele[0].subelements.extend(precinct_increase[ele.name])

      avaele.subelements.remove(pcele)
      avaele.subelements.extend(newele)
      # Add the modified top level element to our write list
      outlist.append(ele)

  write_file(outlist, dirname, outfilename)

# Delete old mod file
def delete_file(fulloutfile):
  try:
    os.unlink(fulloutfile)
  except FileNotFoundError as e:
    pass
  except Exception as e:
    fail("Couldn't delete old file", e)

# Write out the mod file
def write_file(outlist, dirname, outfilename):
  fulloutfile = f"{dirname}/{outfilename}"
  try:
    if not os.path.exists( dirname ):
      os.makedirs( dirname, exist_ok=True )
    with io.open(fulloutfile, 'a', newline="\r\n") as outfile:
      outfile.write(f"# {MOD_NAME}\n")
      outfile.write(cwp.CWToString(outlist))
      outfile.write("\n")
  except Exception as e:
    fail(f"Failed writing, {e}", e)

#######################################
# Turn strings in to CW blocks for later insertion
try:
  enforcer_increase = {}
  enforcer_increase["automate_crime_management"] = cwp.stringToCW(enforcer_increase_str)
  enforcer_increase["automate_crime_management_gestalt"] = cwp.stringToCW(enforcer_increase_gestalt_str)
  precinct_increase = {}
  precinct_increase["automate_crime_management"] = cwp.stringToCW(precinct_increase_str)
  precinct_increase["automate_crime_management_gestalt"] = cwp.stringToCW(precinct_increase_gestalt_str)
  crime_wave = {}
  crime_wave["enforcer"] = cwp.stringToCW(enforcer_wave_str) + cwp.stringToCW(enforcer_branch_str)
  crime_wave["patrol_drone"] = cwp.stringToCW(patrol_drone_wave_str)
except Exception as e:
  fail(e, e)

#######################################
# Main logic
process_crime("common/colony_automation_exceptions/00_crisis_exceptions.txt", "zzz_fl_crime.txt")
process_job("common/pop_jobs/02_specialist_jobs.txt", "99_fl_crime_specialist.txt")
process_job("common/pop_jobs/04_gestalt_jobs.txt", "99_fl_crime_gestalt.txt")
make_descriptor()
make_steamcmd()
