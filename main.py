import functions

all_is_good = functions.check_html_updates()

functions.update_db()
# if not all_is_good:
#     print("Needs updating")
#     functions.update_db()
# else:
#     print("All is good")