# utils/DepartmentReportHandler.py
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
import datetime
import random
from utils.FileStorage import upload_file
from models.Departments import Department
from models.User import User
from models.System_Settings import System_Settings


def create_department_performance_report(department_id, filename_prefix=None):
    """
    Create an Excel sheet showing average performance of members in a department.
    
    Layout:
    - Header: Office name | Performance Assessment: Rating
    - Columns: Name | Numerical | Adjective
    - Data rows with employee ratings
    - Footer: Total, No. of Employees, Average Ratings
    
    Args:
        department_id: The department DB id
        filename_prefix: Optional prefix for filename
    
    Returns:
        download link from FileStorage
    """
    
    # Query department and members
    dept = Department.query.get(department_id)
    if not dept:
        raise ValueError("Department not found")
    
    users = User.query.filter_by(department_id=department_id, account_status=1).all()
    
    # Get system settings for rating thresholds
    settings = System_Settings.query.first()
    rating_thresholds = settings.rating_thresholds if settings else {
        "Outstanding": {"min": 4.5, "max": 5.0},
        "Very Satisfactory": {"min": 3.5, "max": 4.49},
        "Satisfactory": {"min": 2.5, "max": 3.49},
        "Unsatisfactory": {"min": 1.5, "max": 2.49},
        "Poor": {"min": 0, "max": 1.49}
    }
    
    # Create new workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Department Performance"
    
    # Set column widths
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 20
    
    # Define styles
    header_fill = PatternFill(start_color="B4C7E7", end_color="B4C7E7", fill_type="solid")
    header_font = Font(bold=True, size=12)
    border_style = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    total_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
    total_font = Font(bold=True)
    
    # Row 1-3: Headers
    ws.merge_cells('A1:B1')
    ws['A1'] = dept.name
    ws['A1'].font = header_font
    ws['A1'].fill = header_fill
    ws['A1'].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 25
    
    ws.merge_cells('C1:C1')
    ws['C1'] = "Performance Assessment:"
    ws['C1'].font = header_font
    ws['C1'].fill = header_fill
    ws['C1'].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    ws.merge_cells('C2:C2')
    ws['C2'] = "Rating"
    ws['C2'].font = Font(bold=True, size=11)
    ws['C2'].fill = header_fill
    ws['C2'].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[2].height = 20
    
    # Row 4: Column headers
    ws.row_dimensions[3].height = 20
    ws['A3'] = "Name"
    ws['B3'] = "Numerical"
    ws['C3'] = "Adjective"
    
    for col in ['A', 'B', 'C']:
        cell = ws[f'{col}3']
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_style
    
    # Collect member data
    member_data = []
    total_rating = 0
    
    for user in users:
        # Calculate average performance for this user
        # Using IPCR final average if available, otherwise 0
        from models.PCR import IPCR
        active_ipcrs = IPCR.query.filter_by(
            user_id=user.id,
            status=1,
            period=settings.current_period_id if settings else None
        ).all()
        
        if active_ipcrs:
            # Average of all active IPCR ratings
            ratings = [ipcr.final_average_rating for ipcr in active_ipcrs if ipcr.final_average_rating]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0
        else:
            avg_rating = 0
        
        if avg_rating > 0:
            member_data.append({
                'name': f"{user.first_name} {user.middle_name[0] + '.' if user.middle_name else ''} {user.last_name}".strip(),
                'rating': round(avg_rating, 2)
            })
            total_rating += avg_rating
    
    # Sort by name
    member_data.sort(key=lambda x: x['name'])
    
    # Write member data rows
    row = 4
    for member in member_data:
        name = member['name']
        rating = member['rating']
        
        # Determine adjective rating
        adjective = "UNRATED"
        for rating_name, thresholds in rating_thresholds.items():
            min_val = thresholds.get("min", 0)
            max_val = thresholds.get("max", 5)
            if min_val <= rating <= max_val:
                adjective = rating_name
                break
        
        # Write row
        ws[f'A{row}'] = name
        ws[f'B{row}'] = rating
        ws[f'C{row}'] = adjective
        
        # Apply formatting
        for col in ['A', 'B', 'C']:
            cell = ws[f'{col}{row}']
            cell.border = border_style
            cell.alignment = Alignment(horizontal="left" if col == 'A' else "center", vertical="center")
            if col == 'B':
                cell.number_format = '0.00'
        
        row += 1
    
    # Empty row
    row += 1
    
    # Total row
    ws[f'A{row}'] = "Total"
    ws[f'B{row}'] = round(total_rating, 2) if member_data else 0
    
    for col in ['A', 'B']:
        cell = ws[f'{col}{row}']
        cell.font = total_font
        cell.fill = total_fill
        cell.border = border_style
        cell.alignment = Alignment(horizontal="center", vertical="center")
        if col == 'B':
            cell.number_format = '0.00'
    
    row += 1
    
    # No. of Employees row
    ws[f'A{row}'] = "No. of Employees"
    ws[f'B{row}'] = len(member_data)
    
    for col in ['A', 'B']:
        cell = ws[f'{col}{row}']
        cell.font = total_font
        cell.fill = total_fill
        cell.border = border_style
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    row += 1
    
    # Average Ratings row
    avg_rating = total_rating / len(member_data) if member_data else 0
    
    # Determine average adjective
    avg_adjective = "UNRATED"
    for rating_name, thresholds in rating_thresholds.items():
        min_val = thresholds.get("min", 0)
        max_val = thresholds.get("max", 5)
        if min_val <= avg_rating <= max_val:
            avg_adjective = rating_name
            break
    
    ws[f'A{row}'] = "Average Ratings of Staff"
    ws[f'B{row}'] = round(avg_rating, 2)
    ws[f'C{row}'] = avg_adjective
    
    for col in ['A', 'B', 'C']:
        cell = ws[f'{col}{row}']
        cell.font = total_font
        cell.fill = total_fill
        cell.border = border_style
        cell.alignment = Alignment(horizontal="center" if col in ['B', 'C'] else "left", vertical="center")
        if col == 'B':
            cell.number_format = '0.00'
    
    # Save and upload
    id_rand = random.randint(1, 999999)
    prefix = filename_prefix if filename_prefix else "Department Performance"
    period = f"{datetime.datetime.now().strftime('%B %Y')}"
    filename = f"{prefix} - {dept.name} - {period} - {id_rand}"
    
    filepath = f"excels/DepartmentReports/{filename}.xlsx"
    wb.save(filepath)
    
    # Upload to cloud storage
    file_url = upload_file(filepath, "commithub-bucket", f"DepartmentReports/{filename}.xlsx")
    
    return file_url
