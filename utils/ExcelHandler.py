from openpyxl import load_workbook
from openpyxl.styles import Border, Side, Alignment, Font
from openpyxl.drawing.image import Image
import datetime 
from utils.FileStorage import upload_file

import random
from datetime import date
# Load an existing workbook

def formatDate(datestring):
    datestr = str(datestring).split("-")
    
    return f"{datestr[2]}-{datestr[1]}-{datestr[0]}"

def prepareCells(workshop, start, end):
    workshop.merge_cells(f"{start}:{end}")
    
    border_style = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    for row in workshop[f"{start}:{end}"]:
        for cell in row:
            cell.border = border_style


def createNewOPCR(data, assigned, admin_data):
    datee = datetime.datetime.now().month
    year = str(datetime.datetime.now().year)
    period = ""
    if datee <= 6:
        period = "JANUARY - JUNE " + year
    else:
        period = "JULY - DECEMBER " + year
        
    print(admin_data)
    wb = load_workbook("excels/OPCRTest.xlsx")
    ws = wb.active
    
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE

    # Set paper size to A4
    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    # Set all margins to 0
    ws.page_margins.left = 0
    ws.page_margins.right = 0
    ws.page_margins.top = 0
    ws.page_margins.bottom = 0
    ws.page_margins.header = 0
    ws.page_margins.footer = 0

    # Fit all columns in one page (width = 1 page, height = unlimited)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0


    name = admin_data["fullName"]
    ws["A6"] = f"I, {name}, {admin_data["position"]} of the  NORZAGARAY COLLEGE, commit to deliver and agree to be rated on the attainment of "
    ws["A7"] = f"the following targets in accordance with the indicated measures for the period of {period}."
    ws["N8"] = name
    ws["N9"] = admin_data["position"]
    ws["N10"] = formatDate(date.today())
    ws["N10"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["N10"].font = Font(bold=True, name="Calibri", size="11")
    
    ws["A13"] = "Name: " + admin_data["individuals"]["approve"]["name"]
    ws["A14"] = "Position: " +  admin_data["individuals"]["approve"]["position"]
    ws["A15"] = "Date: " + formatDate(admin_data["individuals"]["approve"]["date"])
    
    
    row = 26
    starting = "A"
    
    startingrow = 26
    endrow = 0
    numberformat = "0.00"
    

    for i in data:
        if len(i) == 0: continue
            
        for g, h in i.items():
            if len(h) == 0: continue
            print(g) #category name
            ws[str("A"+str(row))] = g #category name
            ws[str("A"+str(row))].font = Font(bold=True, size=12)
            prepareCells(ws, "A"+str(row), str("S"+str(row)))
            row += 1
            
            for a in h:
                print(a)
                #prepare output cell
                print(str("A"+str(row)))
                prepareCells(ws, str("A"+str(row)) ,str("C"+str(row+5)))
                ws[str("A"+str(row))] = a["title"]
                ws[str("A"+str(row))].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                
                #prepare target cells muna dito 
                prepareCells(ws, str("D"+str(row)), str("D"+str(row + 1)))
                ws["D"+str(row)] = a["summary"]["target"] #quabntity dito
                ws["D"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["D"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("D"+str(row+2)), str("D"+str(row + 3)))
                ws["D"+str(row+2)] = a["working_days"]["target"] #days naman dito
                ws["D"+str(row+2)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["D"+str(row+2)].font = Font(bold=True)
                
                prepareCells(ws, str("D"+str(row+4)), str("D"+str(row + 5)))
                ws["D"+str(row+4)] = a["corrections"]["target"] # corrections 
                ws["D"+str(row+4)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["D"+str(row+4)].font = Font(bold=True)
                
                #description
                prepareCells(ws, str("E"+str(row)), str("G"+str(row + 1)))
                ws["E"+str(row)] = a["description"]["target"] # desc quant 
                ws["E"+str(row)].alignment = Alignment(wrap_text=True, horizontal="left", vertical = "center")
                ws.row_dimensions[row].height = 45
                
                prepareCells(ws, str("E"+str(row+2)), str("G"+str(row + 3)))
                ws["E"+str(row+2)] = a["description"]["time"] + " spent" # desc quant
                
                prepareCells(ws, str("E"+str(row+4)), str("G"+str(row + 5)))
                ws["E"+str(row+4)] = a["description"]["alterations"] # desc quant
                
                #budget alloted
                
                prepareCells(ws, str("H"+str(row)), str("H"+str(row + 5)))
                ws["H"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["H"+str(row)] = 0
                
                #individuals involved
                accountable = ""
                for person in assigned[a["title"]]:
                    accountable += person + "\n"
                
                prepareCells(ws, str("I"+str(row)), str("I"+str(row + 5)))
                ws["I"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["I"+str(row)] = accountable
                
                #prepare dito ng actual cells 
                prepareCells(ws, str("J"+str(row)), str("J"+str(row + 1)))
                ws["J"+str(row)] = a["summary"]["actual"] # desc quant
                ws["J"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["J"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("J"+str(row+2)), str("J"+str(row + 3)))
                ws["J"+str(row+2)] = a["working_days"]["actual"] # desc quant
                ws["J"+str(row+2)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["J"+str(row+2)].font = Font(bold=True)
                
                prepareCells(ws, str("J"+str(row+4)), str("J"+str(row + 5)))
                ws["J"+str(row+4)] = a["corrections"]["actual"] # desc quant
                ws["J"+str(row+4)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["J"+str(row+4)].font = Font(bold=True)
                
                prepareCells(ws, str("K"+str(row)), str("M"+str(row + 1)))
                ws["K"+str(row)] = a["description"]["actual"] # desc quant
                ws["K"+str(row)].alignment = Alignment(wrap_text=True, horizontal="left", vertical = "center")
                
                prepareCells(ws, str("K"+str(row+2)), str("M"+str(row + 3)))
                ws["K"+str(row+2)] = a["description"]["time"] + " spent" # desc quant
                
                prepareCells(ws, str("K"+str(row+4)), str("M"+str(row + 5)))
                ws["K"+str(row+4)] = a["description"]["alterations"] # desc quant
                
                #dito yung ratings
                prepareCells(ws, str("N"+str(row)), str("N"+str(row + 5)))
                ws["N"+str(row)] = a["rating"]["quantity"] # quantity
                ws["N"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["N"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("O"+str(row)), str("O"+str(row + 5)))
                ws["O"+str(row)] = a["rating"]["efficiency"] # timeliness
                ws["O"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["O"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("P"+str(row)), str("P"+str(row + 5)))
                ws["P"+str(row)] = a["rating"]["timeliness"] # corrections
                ws["P"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["P"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("Q"+str(row)), str("Q"+str(row + 5)))
                ws["Q"+str(row)] = a["rating"]["average"] # average
                ws["Q"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["Q"+str(row)].font = Font(bold=True)
                
                #remarks na wala talagang laman
                prepareCells(ws, str("R"+str(row)), str("S"+str(row + 5)))
                ws["R"+str(row)] = " " # remarks
                
                endrow = row
                row = row + 6
    row += 2
    prepareCells(ws, str("L"+str(row)), str("M"+str(row+1)))
    ws["L"+str(row)] = "Final Average Rating"
    ws["L"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("N"+str(row)), str("N"+str(row+1)))
    ws["N"+str(row)] = f"=AVERAGE(N{startingrow+1}: N{endrow})"
    ws["N"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["N"+str(row)].number_format = numberformat
    
    prepareCells(ws, str("O"+str(row)), str("O"+str(row+1)))
    ws["O"+str(row)] = f"=AVERAGE(O{startingrow+1}: O{endrow})"
    ws["O"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["O"+str(row)].number_format = numberformat
    
    prepareCells(ws, str("P"+str(row)), str("P"+str(row+1)))
    ws["P"+str(row)] = f"=AVERAGE(P{startingrow+1}: P{endrow})"
    ws["P"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["P"+str(row)].number_format = numberformat
    
    average = f"=AVERAGE(Q{startingrow}: Q{endrow})"
    averagecell = str("Q"+str(row))
    prepareCells(ws, str("Q"+str(row)), str("Q"+str(row+1)))
    ws["Q"+str(row)] = f"=AVERAGE(Q{startingrow+1}: Q{endrow})"
    ws["Q"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["Q"+str(row)].number_format = numberformat
    
    #final average rating
    row += 2
    prepareCells(ws, str("L"+str(row)), str("M"+str(row+1)))
    ws["L"+str(row)] = "FINAL AVERAGE RATING"
    ws["L"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("N"+str(row)), str("Q"+str(row+1)))
    ws["N"+str(row)] = average
    ws["N"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["N"+str(row)].font = Font(bold=True)
    ws["N"+str(row)].number_format = numberformat    
    
    row += 2
    prepareCells(ws, str("L"+str(row)), str("M"+str(row+1)))
    ws["L"+str(row)] = "ADJECTIVAL RATING"
    ws["L"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("N"+str(row)), str("Q"+str(row+1)))
    ws["N"+str(row)] = f'=IF(AND({averagecell}>=1, {averagecell}<=1.9), "POOR", IF(AND({averagecell}>=2, {averagecell}<=2.9), "UNSATISFACTORY", IF(AND({averagecell}>=3, {averagecell}<=3.9), "SATISFACTORY", IF(AND({averagecell}>=4, {averagecell}<=4.9), "VERY SATISFACTORY", IF(AND({averagecell}=5), "OUTSTANDING")))))'
    ws["N"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["N"+str(row)].font = Font(bold=True)  

    
    #individuals
    row += 3
    prepareCells(ws, str("A"+str(row)), str("D"+str(row)))
    ws["A"+str(row)] = "Discussed With"
    ws["A"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["A"+str(row)].font = Font(bold=True)
    
    prepareCells(ws, str("E"+str(row)), str("F"+str(row)))
    ws["E"+str(row)] = "Date"
    ws["E"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("G"+str(row)), str("J"+str(row)))
    ws["G"+str(row)] = "Assessed By"
    ws["G"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["G"+str(row)].font = Font(bold=True)
    
    prepareCells(ws, str("K"+str(row)), str("L"+str(row)))
    ws["K"+str(row)] = "Date"
    ws["K"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("M"+str(row)), str("P"+str(row)))
    ws["M"+str(row)] = "Final Rating By"
    ws["M"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["M"+str(row)].font = Font(bold=True)
    
    prepareCells(ws, str("Q"+str(row)), str("S"+str(row)))
    ws["Q"+str(row)] = "Date"
    ws["Q"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    row += 1
    
    #adjust row height for individuals
    # name + position
    prepareCells(ws, str("A"+str(row)), str("D"+str(row+2)))
    ws["A"+str(row)] = admin_data["individuals"]["discuss"]["name"] + "\n" + admin_data["individuals"]["discuss"]["position"]
    ws["A"+str(row)].alignment = Alignment(horizontal="center", vertical="bottom", wrap_text=True)
    ws["A"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("E"+str(row)), str("F"+str(row+2)))
    ws["E"+str(row)] = formatDate(admin_data["individuals"]["discuss"]["date"])
    ws["E"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["E"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("G"+str(row)), str("J"+str(row+2)))
    ws["G"+str(row)] = admin_data["individuals"]["assess"]["name"] + "\n" + admin_data["individuals"]["assess"]["position"]
    ws["G"+str(row)].alignment = Alignment(horizontal="center", vertical="bottom", wrap_text=True)
    ws["G"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("K"+str(row)), str("L"+str(row+2)))
    ws["K"+str(row)] = formatDate(admin_data["individuals"]["assess"]["date"])
    ws["K"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["K"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("M"+str(row)), str("P"+str(row+2)))
    ws["M"+str(row)] = admin_data["individuals"]["final"]["name"] + "\n" + admin_data["individuals"]["final"]["position"]
    ws["M"+str(row)].alignment = Alignment(horizontal="center", vertical="bottom", wrap_text=True)
    ws["M"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("Q"+str(row)), str("S"+str(row+2)))
    ws["Q"+str(row)] = formatDate(admin_data["individuals"]["final"]["date"])
    ws["Q"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["Q"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    row+= 4
    
    prepareCells(ws, str("G"+str(row)), str("J"+str(row)))
    ws["G"+str(row)] = "Confirmed By"
    ws["G"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["G"+str(row)].font = Font(bold=True)
    
    prepareCells(ws, str("K"+str(row)), str("L"+str(row)))
    ws["K"+str(row)] = "Date"
    ws["K"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    row += 1
    prepareCells(ws, str("G"+str(row)), str("J"+str(row+2)))
    ws["G"+str(row)] = admin_data["individuals"]["confirm"]["name"] + "\n" + admin_data["individuals"]["confirm"]["position"]
    ws["G"+str(row)].alignment = Alignment(horizontal="center", vertical="bottom", wrap_text=True)
    ws["G"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("K"+str(row)), str("L"+str(row+2)))
    ws["K"+str(row)] = formatDate(admin_data["individuals"]["confirm"]["date"])
    ws["K"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["K"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
            
    #prepare category name    
    # Save changes
    id = random.randint(1,999999)
    filename = f"OPCR-NC-{period}-{admin_data["givenName"]}-{admin_data["middleName"]}-{admin_data["lastName"]}-{datee}-{id}"
    link = f"excels/OPCR/{filename}.xlsx"
    wb.save(link)

    file_url = upload_file(link, "commiathub-bucket", f"OPCR/{filename}.xlsx")
    
    return file_url


 
    
    
def createNewIPCR(data, given, middle, last, individuals, position, dates):
    wb = load_workbook("excels/IPCRTest.xlsx")
    ws = wb.active


    datee = datetime.datetime.now().month
    year = str(datetime.datetime.now().year)
    period = ""
    if datee <= 6:
        period = "JANUARY - JUNE " + year
    else:
        period = "JULY - DECEMBER " + year
    
    
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE

    # Set paper size to A4
    ws.page_setup.paperSize = ws.PAPERSIZE_A4

    # Set all margins to 0
    ws.page_margins.left = 0
    ws.page_margins.right = 0
    ws.page_margins.top = 0
    ws.page_margins.bottom = 0
    ws.page_margins.header = 0
    ws.page_margins.footer = 0

    # Fit all columns in one page (width = 1 page, height = unlimited)
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    
    name = f"{given} {str(middle[0]).capitalize()}. {last}"
    ws["A6"] = f"I, {name}, {position} of the  NORZAGARAY COLLEGE, commit to deliver and agree to be rated on the attainment of "
    ws["A7"] = f"the following targets in accordance with the indicated measures for the period of {period}."
    ws["N8"] = name
    ws["N9"] = position
    ws["N10"] = formatDate(dates)
    ws["N10"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["N10"].font = Font(bold=True, name="Calibri", size="11")
    
    ws["A13"] = individuals["review"]["name"]
    ws["A14"] = individuals["review"]["position"]
    ws["H13"] = formatDate(individuals["review"]["date"])
    ws["H13"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["H13"].font = Font(bold=True, name="Calibri", size="11")
    
    ws["J13"] = individuals["approve"]["name"]
    ws["J14"] = individuals["approve"]["position"]
    ws["R13"] = formatDate(individuals["approve"]["date"])
    ws["R13"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["R13"].font = Font(bold=True, name="Calibri", size="11")
    
    
    row = 26
    starting = "A"
    
    startingrow = 26
    endrow = 0
    numberformat = "0.00"
    

    for i in data:
        if len(i) == 0: continue
            
        for g, h in i.items():
            if len(h) == 0: continue
            print(g) #category name
            ws[str("A"+str(row))] = g #category name
            prepareCells(ws, "A"+str(row), str("S"+str(row)))
            row += 1
            
            for a in h:
                print(a)
                #prepare output cell
                print(str("A"+str(row)))
                prepareCells(ws, str("A"+str(row)) ,str("E"+str(row+5)))
                ws[str("A"+str(row))] = a["title"]
                ws[str("A"+str(row))].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                
                #prepare target cells muna dito 
                prepareCells(ws, str("F"+str(row)), str("F"+str(row + 1)))
                ws["F"+str(row)] = a["summary"]["target"] #quabntity dito
                ws["F"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["F"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("F"+str(row+2)), str("F"+str(row + 3)))
                ws["F"+str(row+2)] = a["working_days"]["target"] #days naman dito
                ws["F"+str(row+2)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["F"+str(row+2)].font = Font(bold=True)
                
                prepareCells(ws, str("F"+str(row+4)), str("F"+str(row + 5)))
                ws["F"+str(row+4)] = a["corrections"]["target"] # corrections 
                ws["F"+str(row+4)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["F"+str(row+4)].font = Font(bold=True)
                
                #description
                prepareCells(ws, str("G"+str(row)), str("I"+str(row + 1)))
                ws["G"+str(row)] = a["description"]["target"] # desc quant 
                ws["G"+str(row)].alignment = Alignment(wrap_text=True, horizontal="left", vertical = "center")
                ws.row_dimensions[row].height = 45
                
                prepareCells(ws, str("G"+str(row+2)), str("I"+str(row + 3)))
                ws["G"+str(row+2)] = a["description"]["time"] + " spent" # time quant
                
                prepareCells(ws, str("G"+str(row+4)), str("I"+str(row + 5)))
                ws["G"+str(row+4)] = a["description"]["alterations"]  # correct quant
                
                #prepare dito ng actual cells 
                prepareCells(ws, str("J"+str(row)), str("J"+str(row + 1)))
                ws["J"+str(row)] = a["summary"]["actual"] # desc quant
                ws["J"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["J"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("J"+str(row+2)), str("J"+str(row + 3)))
                ws["J"+str(row+2)] = a["working_days"]["actual"] # desc quant
                ws["J"+str(row+2)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["J"+str(row+2)].font = Font(bold=True)
                
                prepareCells(ws, str("J"+str(row+4)), str("J"+str(row + 5)))
                ws["J"+str(row+4)] = a["corrections"]["actual"] # desc quant
                ws["J"+str(row+4)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["J"+str(row+4)].font = Font(bold=True)
                
                prepareCells(ws, str("K"+str(row)), str("M"+str(row + 1)))
                ws["K"+str(row)] = a["description"]["actual"] # desc quant
                ws["K"+str(row)].alignment = Alignment(wrap_text=True, horizontal="left", vertical = "center")
                
                prepareCells(ws, str("K"+str(row+2)), str("M"+str(row + 3)))
                ws["K"+str(row+2)] = a["description"]["time"] + " spent" # desc quant
                
                prepareCells(ws, str("K"+str(row+4)), str("M"+str(row + 5)))
                ws["K"+str(row+4)] = a["description"]["alterations"] # desc quant
                
                #dito yung ratings
                prepareCells(ws, str("N"+str(row)), str("N"+str(row + 5)))
                ws["N"+str(row)] = a["rating"]["quantity"] # quantity
                ws["N"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["N"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("O"+str(row)), str("O"+str(row + 5)))
                ws["O"+str(row)] = a["rating"]["efficiency"] # timeliness
                ws["O"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["O"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("P"+str(row)), str("P"+str(row + 5)))
                ws["P"+str(row)] = a["rating"]["timeliness"] # corrections
                ws["P"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["P"+str(row)].font = Font(bold=True)
                
                prepareCells(ws, str("Q"+str(row)), str("Q"+str(row + 5)))
                ws["Q"+str(row)] = a["rating"]["average"] # average
                ws["Q"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                ws["Q"+str(row)].font = Font(bold=True)
                
                #remarks na wala talagang laman
                prepareCells(ws, str("R"+str(row)), str("S"+str(row + 5)))
                ws["R"+str(row)] = " " # remarks
                
                endrow = row
                row = row + 6
    row += 2
    prepareCells(ws, str("L"+str(row)), str("M"+str(row+1)))
    ws["L"+str(row)] = "Final Average Rating"
    ws["L"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("N"+str(row)), str("N"+str(row+1)))
    ws["N"+str(row)] = f"=AVERAGE(N{startingrow}: N{endrow})"
    ws["N"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["N"+str(row)].number_format = numberformat
    
    prepareCells(ws, str("O"+str(row)), str("O"+str(row+1)))
    ws["O"+str(row)] = f"=AVERAGE(O{startingrow}: O{endrow})"
    ws["O"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["O"+str(row)].number_format = numberformat
    
    prepareCells(ws, str("P"+str(row)), str("P"+str(row+1)))
    ws["P"+str(row)] = f"=AVERAGE(P{startingrow}: P{endrow})"
    ws["P"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["P"+str(row)].number_format = numberformat
    
    average = f"=AVERAGE(Q{startingrow}: Q{endrow})"
    averagecell = str("Q"+str(row))
    prepareCells(ws, str("Q"+str(row)), str("Q"+str(row+1)))
    ws["Q"+str(row)] = f"=AVERAGE(Q{startingrow}: Q{endrow})"
    ws["Q"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["Q"+str(row)].number_format = numberformat
    
    #final average rating
    row += 2
    prepareCells(ws, str("L"+str(row)), str("M"+str(row+1)))
    ws["L"+str(row)] = "FINAL AVERAGE RATING"
    ws["L"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("N"+str(row)), str("Q"+str(row+1)))
    ws["N"+str(row)] = average
    ws["N"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["N"+str(row)].font = Font(bold=True)
    ws["N"+str(row)].number_format = numberformat    
    
    row += 2
    prepareCells(ws, str("L"+str(row)), str("M"+str(row+1)))
    ws["L"+str(row)] = "ADJECTIVAL RATING"
    ws["L"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("N"+str(row)), str("Q"+str(row+1)))
    ws["N"+str(row)] = f'=IF(AND({averagecell}>=1, {averagecell}<=1.9), "POOR", IF(AND({averagecell}>=2, {averagecell}<=2.9), "UNSATISFACTORY", IF(AND({averagecell}>=3, {averagecell}<=3.9), "SATISFACTORY", IF(AND({averagecell}>=4, {averagecell}<=4.9), "VERY SATISFACTORY", IF(AND({averagecell}=5), "OUTSTANDING")))))'
    ws["N"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["N"+str(row)].font = Font(bold=True)  

    
    #individuals
    row += 3
    prepareCells(ws, str("A"+str(row)), str("D"+str(row)))
    ws["A"+str(row)] = "Discussed With"
    ws["A"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["A"+str(row)].font = Font(bold=True)
    
    prepareCells(ws, str("E"+str(row)), str("F"+str(row)))
    ws["E"+str(row)] = "Date"
    ws["E"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("G"+str(row)), str("J"+str(row)))
    ws["G"+str(row)] = "Assessed By"
    ws["G"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["G"+str(row)].font = Font(bold=True)
    
    prepareCells(ws, str("K"+str(row)), str("L"+str(row)))
    ws["K"+str(row)] = "Date"
    ws["K"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    prepareCells(ws, str("M"+str(row)), str("P"+str(row)))
    ws["M"+str(row)] = "Final Rating By"
    ws["M"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["M"+str(row)].font = Font(bold=True)
    
    prepareCells(ws, str("Q"+str(row)), str("S"+str(row)))
    ws["Q"+str(row)] = "Date"
    ws["Q"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    
    
    
    
    row += 1
    
    #adjust row height for individuals
    # name + position
    prepareCells(ws, str("A"+str(row)), str("D"+str(row+2)))
    ws["A"+str(row)] = f"{individuals["discuss"]["name"]}\n{individuals["discuss"]["position"]}"
    ws["A"+str(row)].alignment = Alignment(horizontal="center", vertical="bottom", wrap_text=True)
    ws["A"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("E"+str(row)), str("F"+str(row+2)))
    ws["E"+str(row)] = formatDate(individuals["discuss"]["date"])
    ws["E"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["E"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("G"+str(row)), str("J"+str(row+2)))
    ws["G"+str(row)] = f"{individuals["assess"]["name"]}\n{individuals["assess"]["position"]}"
    ws["G"+str(row)].alignment = Alignment(horizontal="center", vertical="bottom", wrap_text=True)
    ws["G"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("K"+str(row)), str("L"+str(row+2)))
    ws["K"+str(row)] = formatDate(individuals["assess"]["date"])
    ws["K"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["K"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("M"+str(row)), str("P"+str(row+2)))
    ws["M"+str(row)] = f"{individuals["final"]["name"]}\n{individuals["final"]["position"]}"
    ws["M"+str(row)].alignment = Alignment(horizontal="center", vertical="bottom", wrap_text=True)
    ws["M"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("Q"+str(row)), str("S"+str(row+2)))
    ws["Q"+str(row)] = formatDate(individuals["final"]["date"])
    ws["Q"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["Q"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    row+= 4
    
    prepareCells(ws, str("G"+str(row)), str("J"+str(row)))
    ws["G"+str(row)] = "Confirmed By"
    ws["G"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["G"+str(row)].font = Font(bold=True)
    
    prepareCells(ws, str("K"+str(row)), str("L"+str(row)))
    ws["K"+str(row)] = "Date"
    ws["K"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    row += 1
    prepareCells(ws, str("G"+str(row)), str("J"+str(row+2)))
    ws["G"+str(row)] = f"{individuals["confirm"]["name"]}\n{individuals["confirm"]["position"]}"
    ws["G"+str(row)].alignment = Alignment(horizontal="center", vertical="bottom", wrap_text=True)
    ws["G"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
    prepareCells(ws, str("K"+str(row)), str("L"+str(row+2)))
    ws["K"+str(row)] = formatDate(individuals["confirm"]["date"])
    ws["K"+str(row)].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws["K"+str(row)].font = Font(bold=True, name="Calibri", size="11")
    
            
    #prepare category name    
    # Save changes
    id = random.randint(1,999999)
    filename = f"IPCR-NC-{period}-{given}-{middle}-{last}-{datee}-{id}"
    link = f"excels/IPCR/{filename}.xlsx"
    wb.save(link)
    
    return "downloadlink"
    