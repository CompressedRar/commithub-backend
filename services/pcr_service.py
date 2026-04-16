"""
PCR_Service facade — preserves the original public API.
Delegates to focused service modules.
"""

from services.PCR.pcr_rating_service import PCRRatingService
from services.PCR.pcr_crud_service import PCRCRUDService
from services.PCR.pcr_workflow_service import PCRWorkflowService
from services.PCR.pcr_generation_service import PCRGenerationService
from services.PCR.pcr_analytics_service import PCRAnalyticsService


class PCR_Service:
    # Rating helpers
    compute_rating_with_override        = staticmethod(PCRRatingService.compute_rating_with_override)
    compute_quantity_rating             = staticmethod(PCRRatingService.compute_quantity_rating)
    compute_efficiency_rating           = staticmethod(PCRRatingService.compute_efficiency_rating)
    compute_timeliness_rating           = staticmethod(PCRRatingService.compute_timeliness_rating)
    calculateQuantity                   = staticmethod(PCRRatingService.calculateQuantity)
    calculateEfficiency                 = staticmethod(PCRRatingService.calculateEfficiency)
    calculateTimeliness                 = staticmethod(PCRRatingService.calculateTimeliness)
    calculateAverage                    = staticmethod(PCRRatingService.calculateAverage)
    compute_and_save_opcr_ratings       = staticmethod(PCRGenerationService.compute_and_save_opcr_ratings)

    # CRUD
    generate_IPCR_from_tasks            = staticmethod(PCRCRUDService.generate_IPCR_from_tasks)
    generate_IPCR                       = staticmethod(PCRCRUDService.generate_IPCR)
    create_opcr                         = staticmethod(PCRCRUDService.create_opcr)
    get_ipcr                            = staticmethod(PCRCRUDService.get_ipcr)
    assign_main_ipcr                    = staticmethod(PCRCRUDService.assign_main_ipcr)
    assign_pres_ipcr                    = staticmethod(PCRCRUDService.assign_pres_ipcr)
    assign_main_opcr                    = staticmethod(PCRCRUDService.assign_main_opcr)
    archive_ipcr                        = staticmethod(PCRCRUDService.archive_ipcr)
    archive_opcr                        = staticmethod(PCRCRUDService.archive_opcr)
    update_rating                       = staticmethod(PCRCRUDService.update_rating)
    record_supporting_document          = staticmethod(PCRCRUDService.record_supporting_document)
    get_ipcr_supporting_document        = staticmethod(PCRCRUDService.get_ipcr_supporting_document)
    get_supporting_documents            = staticmethod(PCRCRUDService.get_supporting_documents)
    archive_document                    = staticmethod(PCRCRUDService.archive_document)
    collect_all_supporting_documents_by_department = staticmethod(PCRCRUDService.collect_all_supporting_documents_by_department)
    collect_all_supporting_documents    = staticmethod(PCRCRUDService.collect_all_supporting_documents)

    # Workflow
    reject_ipcr                         = staticmethod(PCRWorkflowService.reject_ipcr)
    review_ipcr                         = staticmethod(PCRWorkflowService.review_ipcr)
    approve_ipcr                        = staticmethod(PCRWorkflowService.approve_ipcr)
    reject_opcr                         = staticmethod(PCRWorkflowService.reject_opcr)
    review_opcr                         = staticmethod(PCRWorkflowService.review_opcr)
    approve_opcr                        = staticmethod(PCRWorkflowService.approve_opcr)
    get_member_pendings                 = staticmethod(PCRWorkflowService.get_member_pendings)
    get_member_reviewed                 = staticmethod(PCRWorkflowService.get_member_reviewed)
    get_member_approved                 = staticmethod(PCRWorkflowService.get_member_approved)
    get_head_pendings                   = staticmethod(PCRWorkflowService.get_head_pendings)
    get_head_reviewed                   = staticmethod(PCRWorkflowService.get_head_reviewed)
    get_head_approved                   = staticmethod(PCRWorkflowService.get_head_approved)
    get_opcr_pendings                   = staticmethod(PCRWorkflowService.get_opcr_pendings)
    get_opcr_reviewed                   = staticmethod(PCRWorkflowService.get_opcr_reviewed)
    get_opcr_approved                   = staticmethod(PCRWorkflowService.get_opcr_approved)
    reject_supporting_document          = staticmethod(PCRWorkflowService.reject_supporting_document)
    approve_supporting_document         = staticmethod(PCRWorkflowService.approve_supporting_document)

    # Generation
    get_opcr                            = staticmethod(PCRGenerationService.get_opcr)
    get_planned_opcr_by_department      = staticmethod(PCRGenerationService.get_planned_opcr_by_department)
    get_master_opcr                     = staticmethod(PCRGenerationService.get_master_opcr)
    generate_opcr                       = staticmethod(PCRGenerationService.generate_opcr)
    generate_weighted_opcr              = staticmethod(PCRGenerationService.generate_weighted_opcr)
    generate_planned_opcr_by_department = staticmethod(PCRGenerationService.generate_planned_opcr_by_department)
    generate_master_opcr                = staticmethod(PCRGenerationService.generate_master_opcr)
    new_generate_opcr                   = staticmethod(PCRGenerationService.new_generate_opcr)

    # Analytics
    get_department_performance_summary  = staticmethod(PCRAnalyticsService.get_department_performance_summary)
    get_performance_history             = staticmethod(PCRAnalyticsService.get_performance_history)
    get_performance_trends              = staticmethod(PCRAnalyticsService.get_performance_trends)
    get_comparative_analytics           = staticmethod(PCRAnalyticsService.get_comparative_analytics)
    get_performance_forecast            = staticmethod(PCRAnalyticsService.get_performance_forecast)
    get_kpi_status                      = staticmethod(PCRAnalyticsService.get_kpi_status)
    get_offices_opcr_progress           = staticmethod(PCRAnalyticsService.get_offices_opcr_progress)
