import gspread 

def add_values_to_google_sheet(row):
    gc = gspread.service_account(filename='static/level-elevator-352213-89f1232c4be1.json')
    sh = gc.open('BookNow').sheet1
    sh.append_row(row)
    return