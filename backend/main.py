import functions

functions.update_db()
all_is_good = functions.check_html_updates()

if not all_is_good:
    print("Needs updating")
    functions.update_db()
else:
    print("All is good")

print(len(functions.run()))