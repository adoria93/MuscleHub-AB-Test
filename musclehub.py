# Like most businesses, the data is in a SQL database. Each SQL query will be put into a function called 'sql_query'
# from the codecademySQL package.

from codecademySQL import sql_query

# Get the dataset

# Tables available:
#
# - `visits` contains information about potential gym customers who have visited MuscleHub
# - `fitness_tests` contains information about potential customers in "Group A", who were given a fitness test
# - `applications` contains information about any potential customers (both "Group A" and "Group B") who filled out an application.  
#      Not everyone in `visits` will have filled out an application.
# - `purchases` contains information about customers who purchased a membership to MuscleHub.

# Taking a look at each of the tables

sql_query('''
SELECT *
FROM visits
LIMIT 5
''')

sql_query('''
SELECT *
FROM fitness_tests
LIMIT 5
''')

sql_query('''
SELECT *
FROM applications
LIMIT 5
''')

sql_query('''
SELECT *
FROM purchases
LIMIT 5
''')

# Joining the tables
#
# 1. Not all visits in `visits` occurred during the A/B test.  (A/B test started July 2017)
# 2. Each table includes information about a person, but each table does not assign a unique ID to each person.
#     In order to merge these tables correctly, a merge on first_name, last_name, and email must be done to make
#     sure that each row represents only one person.
# 
# Columns of interest:
#
# - `visits.first_name`
# - `visits.last_name`
# - `visits.gender`
# - `visits.email`
# - `visits.visit_date`
# - `fitness_tests.fitness_test_date`
# - `applications.application_date`
# - `purchases.purchase_date`

df = sql_query('''
SELECT visits.first_name,
        visits.last_name,
        visits.gender,
        visits.email,
        visits.visit_date,
        fitness_tests.fitness_test_date,
        applications.application_date,
        purchases.purchase_date
FROM visits
LEFT JOIN fitness_tests
    ON visits.first_name = fitness_tests.first_name
    AND visits.last_name = fitness_tests.last_name
    AND visits.email = fitness_tests.email
LEFT JOIN applications
    ON visits.first_name = applications.first_name
    AND visits.last_name = applications.last_name
    AND visits.email = applications.email
LEFT JOIN purchases
    ON visits.first_name = purchases.first_name
    AND visits.last_name = purchases.last_name
    AND visits.email = purchases.email
WHERE visits.visit_date >= '7-1-17'
''')

# Note: Normally this would be done in SQL and saved as a csv that would then
# be imported into python using Pandas. Because I have access to that codecademySQL package,
# I'm able to treat this just as a python project.

#------------------------------------------

# Investigate the A and B groups

import pandas as pd
from matplotlib import pyplot as plt

# Adding a column to the dataframe called "ab_test_group". Group A is the group that had to take a fitness test, Group B did not

df["ab_test_group"] = df.fitness_test_date.apply(lambda x: "A" if pd.notnull(x) else "B")


# Checking to make sure that about half are in Group A and half are in group B

ab_counts = df.groupby("ab_test_group").first_name.count().reset_index()
ab_counts

# Creating a pie chart to visualize this information

plt.pie(ab_counts.first_name.values, labels= ["A", "B"], autopct= '%0.2f%%')
plt.axis("equal")
plt.savefig("ab_test_pie_chart.png")
plt.show()

#----------------------------------------------------------

# Who picks up an application?

# The sign-up process for MuscleHub has several steps:
#   1. Take a fitness test with a personal trainer (only Group A)
#   2. Fill out an application for the gym
#   3. Send in their payment for their first month's membership
# 
# How many people make it to Step 2, filling out an application.

# Creating  new column to track applications. Column will contain "Application" if the application_date is not missing.

df["is_application"] = df.application_date.apply(lambda x: "Application" if pd.notnull(x) else "No Application")

# Counting how many people in each group

app_counts = df.groupby(["ab_test_group", "is_application"]).first_name.count().reset_index()
app_counts

# Calculating the percent of people in each group who complete the application

app_pivot = app_counts.pivot(columns="is_application", index= "ab_test_group",values="first_name").reset_index()

app_pivot["Total"] = app_pivot.Application + app_pivot["No Application"]
app_pivot["Percent with Application"] = app_pivot.Application / app_pivot.Total

app_pivot

# It looks like Group B turned in more applications. Using the chi2_contingency test, taking a look to 
# see if this difference between the two groups is significant.

from scipy.stats import chi2_contingency

# Creating the table for the test

contingency = [[250, 2254],
              [325, 2175]]

chi2_contingency(contingency)

# Test Output: (10.893961295282612,
                 0.0009647827600722304,
                 1,
        array([[ 287.72981615, 2216.27018385],
                [ 287.27018385, 2212.72981615]]))

#------------------------------------------------------
              
# Who purchases a membership?

# Of those who picked up an application, how many purchased a membership?
# 
# Let's begin by adding a column to `df` called `is_member` which is `Member` if `purchase_date` is not `None`, and `Not Member` otherwise.

# In[42]:

# Creating a new column to track if a person is a member or not

df["is_member"] = df.purchase_date.apply(lambda x: "Member" if pd.notnull(x) else "Not Member")

# Creating a new dataframe that contains only those who picked up an application

just_apps = df[df.is_application == "Application"]
just_apps.head()

# Following a similar process that was done above to determine the percentage that purchase

member_count = just_apps.groupby(["ab_test_group", "is_member"]).first_name.count().reset_index()
member_count

member_pivot = member_count.pivot(columns= "is_member", index= "ab_test_group", values="first_name").reset_index()

member_pivot["Total"] = member_pivot.Member + member_pivot["Not Member"]
member_pivot["Percent Purchase"] = member_pivot.Member / member_pivot.Total

member_pivot


# It looks like people who took the fitness test were more likely to purchase a membership **if** they picked up an application.
# Testing to see if this difference is significant or not.

member_table = [[200, 50],
               [250, 75]]

chi2_contingency(member_table)

# Test Output: (0.615869230769231,
                0.43258646051083327,
                1,
        array([[195.65217391,  54.34782609],
                [254.34782609,  70.65217391]]))
                
#----------------------------------------------------------

# What percentage of **all visitors** purchased memberships.
# Silmilar process as above 

final_member = df.groupby(["ab_test_group", "is_member"]).first_name.count().reset_index()
final_member_pivot = final_member.pivot(columns= "is_member", index= "ab_test_group", values= "first_name").reset_index()

final_member_pivot["Total"] = final_member_pivot.Member + final_member_pivot["Not Member"]
final_member_pivot["Percent Purchase"] = final_member_pivot.Member / final_member_pivot.Total

final_member_pivot


# When we only considered people who had **already picked up an application**, we saw that there was no significant difference in membership
# between Group A and Group B.
# 
# Now, considering all people who **visit MuscleHub**, is this difference significant?

final_member_table = [[200, 2304],
                     [250, 2250]]

chi2_contingency(final_member_table)

# Test Output: (5.949182292591156,
                0.014724114645783203,
                1,
        array([[ 225.17985612, 2278.82014388],
                [ 224.82014388, 2275.17985612]]))

#--------------------------------------------------------------

# Summarize the acquisition funel with a chart

# Making a bar chart for Janet that shows the difference between Group A (people who were given the fitness test)
# and Group B (people who were not given the fitness test) at each state of the process:
#
# - Percent of visitors who apply
# - Percent of applicants who purchase a membership
# - Percent of visitors who purchase a membership

# Percent of **Visitors** who Apply

ax = plt.subplot()
plt.bar(range(len(app_pivot)),
       app_pivot["Percent with Application"].values)
       
ax.set_xticks(range(len(app_pivot)))
ax.set_xticklabels(["Fitness Test", "No Fitness Test"])

ax.set_yticks([0, 0.05, 0.10, 0.15, 0.20])
ax.set_yticklabels(["0%", "5%", "10%", "15%", "20%"])

plt.title("Percent of Visitors who Apply")

plt.savefig("percent_visitors_apply.png")

plt.show()


# Percent of **Applicants** who Purchase

ax = plt.subplot()
plt.bar(range(len(member_pivot)),
       member_pivot["Percent Purchase"].values)
       
ax.set_xticks(range(len(app_pivot)))
ax.set_xticklabels(["Fitness Test", "No Fitness Test"])

ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
ax.set_yticklabels(["0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%"])

plt.title("Percent of Applicants who Purchase Membership")

plt.savefig("percent_apply_purchase.png")

plt.show()


# Percent of **Visitors** who Purchase

ax = plt.subplot()

plt.bar(range(len(final_member_pivot)),
       final_member_pivot["Percent Purchase"].values)
       
ax.set_xticks(range(len(app_pivot)))
ax.set_xticklabels(["Fitness Test", "No Fitness Test"])

ax.set_yticks([0, 0.05, 0.10, 0.15, 0.20])
ax.set_yticklabels(["0%", "5%", "10%", "15%", "20%"])

plt.title("Percent of Vistors who Purchase Membership")

plt.savefig("percent_visitors_purchase.png")

plt.show()
