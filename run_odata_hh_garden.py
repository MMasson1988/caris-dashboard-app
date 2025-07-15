import os
import re
import time
import pandas as pd
import numpy as np
from utils import get_commcare_odata
from ptme_fonction import creer_colonne_match_conditional

# Garden database
garden_household__url ='https://www.commcarehq.org/a/caris-test/api/odata/cases/v1/30eff12a21b721802a814346a46bd970/feed'
# Define the headers for the request
auth = (os.getenv('CC_USERNAME'), os.getenv('CC_PASSWORD'))
# Define parameters to filter inactive, non-graduated groups
params = {}
garden_household = get_commcare_odata(garden_household__url, auth, params)
garden_household = pd.DataFrame(garden_household)
garden_household.columns = [col.replace(' ', '_') for col in garden_household.columns]
garden_household = garden_household[['indices_Garden','age_in_year','gender','gardining_member_relationship','hiv_test','hiv_test_date','hiv_test_result','is_on_arv','risk_level','referred_for_a_test','test_institution']]
garden_household.to_excel('garden_household.xlsx', index=True)
