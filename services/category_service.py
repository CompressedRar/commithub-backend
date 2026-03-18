"""
Category_Service facade — preserves the original public API.
Delegates to the focused service modules.
"""

from services.Category.category_crud_service import CategoryCRUDService
from services.Category.category_performance_service import CategoryPerformanceService


class Category_Service:
    # CRUD
    get_all                                     = staticmethod(CategoryCRUDService.get_all)
    get_all_with_tasks                          = staticmethod(CategoryCRUDService.get_all_with_tasks)
    get_category                                = staticmethod(CategoryCRUDService.get_category)
    get_category_count                          = staticmethod(CategoryCRUDService.get_category_count)
    create_category                             = staticmethod(CategoryCRUDService.create_category)
    update_category                             = staticmethod(CategoryCRUDService.update_category)
    update_category_order                       = staticmethod(CategoryCRUDService.update_category_order)
    archive_category                            = staticmethod(CategoryCRUDService.archive_category)

    # Performance
    get_task_average_summary                    = staticmethod(CategoryPerformanceService.get_task_average_summary)
    calculate_category_performance              = staticmethod(CategoryPerformanceService.calculate_category_performance)
    calculate_category_performance_per_department = staticmethod(CategoryPerformanceService.calculate_category_performance_per_department)
