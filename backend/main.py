import functions

all_is_good = functions.check_html_updates()

if not all_is_good:
    functions.update_db()
    functions.onChange()

functions.update_db()