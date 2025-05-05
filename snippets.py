# Mod snippets
CRIME_WAVE_THRESH = 10 # crime.41
GOOD_STABILITY_THRESH = "@stabilitylevel3" # 40. High stability factor
BAD_STABILITY_THRESH = "@stabilitylevel2" # 25. Revolt possible
VERY_BAD_STABILITY_THRESH = "@stabilitylevel1" # 10. Only used in unrest.110 ?
SYNDICATE_THRESH = 0 # crime.1000/1001

enforcer_increase_str = f"""
                enforcer_increase = {{
                        available = {{
                                OR = {{
                                    planet_stability < {VERY_BAD_STABILITY_THRESH}
                                    AND = {{
                                        planet_crime > {CRIME_WAVE_THRESH}
                                        OR = {{
                                            has_modifier = criminal_underworld
                                            has_modifier = gang_wars
                                            has_modifier = center_of_drug_trade
                                            has_modifier = mob_rule
                                        }}
                                    }}
                                    AND = {{
                                        planet_crime > {SYNDICATE_THRESH}
                                        has_branch_office = yes
                                        branch_office_owner = {{
                                            is_criminal_syndicate = yes
                                        }}
                                    }}
                                }}
                        }}

                        job = enforcer
                        amount = 1
                }}
"""
enforcer_increase_gestalt_str = f"""
                job_patrol_drone_add_increase = {{
                        available = {{
                                        planet_crime > {CRIME_WAVE_THRESH}
                                        OR = {{
                                            has_modifier = drone_deviancy
                                            has_modifier = drone_corruption
                                        }}
                                    }}

                        job = patrol_drone
                        amount = 1
                }}
"""
precinct_increase_str = f"""
                    planet_stability < {BAD_STABILITY_THRESH}
                    AND = {{
                        planet_crime > {CRIME_WAVE_THRESH}
                        OR = {{
                            has_modifier = criminal_underworld
                            has_modifier = gang_wars
                            has_modifier = center_of_drug_trade
                            has_modifier = mob_rule
                        }}
                    }}
                    AND = {{
                        planet_crime > {SYNDICATE_THRESH}
                        has_branch_office = yes
                        branch_office_owner = {{
                            is_criminal_syndicate = yes
                        }}
                    }}
"""
precinct_increase_gestalt_str = f"""
                    AND = {{
                        planet_crime > {CRIME_WAVE_THRESH}
                        OR = {{
                            has_modifier = drone_deviancy
                            has_modifier = drone_corruption
                        }}
                    }}
"""
patrol_drone_wave_str = f"""
                modifier = {{
                        factor = 20
                        planet = {{ 
                            OR = {{
                                has_modifier = drone_deviancy
                                has_modifier = drone_corruption
                            }}
                        }}
                }}
"""
enforcer_wave_str = f"""
                modifier = {{
                        factor = 40
                        planet = {{
                            OR = {{
                                has_modifier = criminal_underworld
                                has_modifier = gang_wars
                                has_modifier = center_of_drug_trade
                                has_modifier = mob_rule
                            }}
                        }}
                }}
"""
enforcer_branch_str = f"""
                modifier = {{
                        factor = 75
                        planet = {{
                            has_branch_office = yes
                            branch_office_owner = {{
                                is_criminal_syndicate = yes
                            }}
                        }}
                }}
"""
enforcer_stability_str = f"""
                modifier = {{
                        factor = 2
                        planet = {{ planet_stability < {GOOD_STABILITY_THRESH} }}
                }}
                modifier = {{
                        factor = 10
                        planet = {{ planet_stability < {BAD_STABILITY_THRESH} }}
                }}
                modifier = {{
                        factor = 20
                        planet = {{ planet_stability < {VERY_BAD_STABILITY_THRESH} }}
                }}
"""
