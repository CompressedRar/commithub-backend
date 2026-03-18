"""
Tasks_Service facade — preserves the original public API.
Delegates to the focused service modules.
"""

from services.Tasks.task_crud_service import TaskCRUDService
from services.Tasks.task_assignment_service import TaskAssignmentService
from services.Tasks.task_query_service import TaskQueryService
from services.Tasks.task_performance_service import TaskPerformanceService


class Tasks_Service:
    # CRUD
    get_main_tasks                  = staticmethod(TaskCRUDService.get_main_tasks)
    get_main_task                   = staticmethod(TaskCRUDService.get_main_task)
    get_all_tasks_count             = staticmethod(TaskCRUDService.get_all_tasks_count)
    create_main_task                = staticmethod(TaskCRUDService.create_main_task)
    update_task_info                = staticmethod(TaskCRUDService.update_task_info)
    archive_task                    = staticmethod(TaskCRUDService.archive_task)
    update_tasks_weights            = staticmethod(TaskCRUDService.update_tasks_weights)
    update_assigned_dept            = staticmethod(TaskCRUDService.update_assigned_dept)
    update_department_task_formula  = staticmethod(TaskCRUDService.update_department_task_formula)

    # Assignment
    assign_user                     = staticmethod(TaskAssignmentService.assign_user)
    unassign_user                   = staticmethod(TaskAssignmentService.unassign_user)
    assign_department               = staticmethod(TaskAssignmentService.assign_department)
    remove_task_from_dept           = staticmethod(TaskAssignmentService.remove_task_from_dept)
    create_user_output              = staticmethod(TaskAssignmentService.create_user_output)
    create_task_for_ipcr            = staticmethod(TaskAssignmentService.create_task_for_ipcr)
    remove_output_by_main_task_id   = staticmethod(TaskAssignmentService.remove_output_by_main_task_id)

    # Queries
    get_assigned_department             = staticmethod(TaskQueryService.get_assigned_department)
    get_assigned_departments_for_opcr   = staticmethod(TaskQueryService.get_assigned_departments_for_opcr)
    get_tasks_by_department             = staticmethod(TaskQueryService.get_tasks_by_department)
    get_department_task                 = staticmethod(TaskQueryService.get_department_task)
    get_assigned_users                  = staticmethod(TaskQueryService.get_assigned_users)
    get_general_assigned_users          = staticmethod(TaskQueryService.get_general_assigned_users)
    get_general_tasks                   = staticmethod(TaskQueryService.get_general_tasks)
    get_all_general_tasks               = staticmethod(TaskQueryService.get_all_general_tasks)

    # Performance
    calculateQuantity                   = staticmethod(TaskPerformanceService.calculateQuantity)
    calculateEfficiency                 = staticmethod(TaskPerformanceService.calculateEfficiency)
    calculateTimeliness                 = staticmethod(TaskPerformanceService.calculateTimeliness)
    calculateAverage                    = staticmethod(TaskPerformanceService.calculateAverage)
    update_sub_task_fields              = staticmethod(TaskPerformanceService.update_sub_task_fields)
    get_task_user_averages              = staticmethod(TaskPerformanceService.get_task_user_averages)
    get_department_subtask_percentage   = staticmethod(TaskPerformanceService.get_department_subtask_percentage)
    calculate_main_task_performance     = staticmethod(TaskPerformanceService.calculate_main_task_performance)
    calculate_user_performance          = staticmethod(TaskPerformanceService.calculate_user_performance)
    get_all_tasks_average_summary       = staticmethod(TaskPerformanceService.get_all_tasks_average_summary)
    calculate_all_tasks_average_summary = staticmethod(TaskPerformanceService.calculate_all_tasks_average_summary)
    get_user_performance_history        = staticmethod(TaskPerformanceService.get_user_performance_history)
