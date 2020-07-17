# final_project_cs50
The website allows people to buy and sell study notes. What is special about this website is the "Leaderboard" feature which, to the best of my knowledge, does not exist on other similar websites. It allows people to search for sellers of apps and sorts them via certain criteria (such as average review score). Then, it is possible to view a seller's profile which includes their social media (if they choose to have them public) as well as their contact email. This way, it is possible to contact notes of sellers directly and organize one-on-one tutorials or even ask them questions about their notes directly.

Rising to the top of the Leaderboards can incentivize sellers to not only charge a low price, but also, to increase the quality of their notes.

Login details are stored in a separate database in my computer. When a user tries to log in, his input is checked with the correct input from the database.

When a new user registers for the first time, the code checks if the username or email have already been taken to avoid duplicates.

When someone tries to sell notes, the file uploaded is stored in my computer in a specific folder. The path of the folder where the file is saved is created dynamically by combining the input the user inputs in the "/sell" page. This way, it is easy to then download the correct file since everything is stored in a meaningful path.

The "/leaderboard" page allows the users to insert some criteria in order to view the leaderboard of sellers from a specific university or program. The sellers are then sorted according to the average review score they have received for all the notes they have uploaded. All profiles can be viewed in detail so that a buyer can ask any questions he/she wants to the seller directly via email or any other social media.

The "/search_profile" page allows users to search for other people directly, without needing to find them via the "/leaderboard" page.

The "/account" page allows users to view and edit their user-details. They can also view the files they have uploaded and download them.