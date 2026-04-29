def start_schedulers():
    from schedulers.breeding_recommendation_scheduler import start_breeding_recommendation_scheduler
    from schedulers.competitor_scheduler import start_competitor_scheduler
    from schedulers.alert_detail_scheduler import start_alert_detail_scheduler
    from schedulers.alert_scheduler import start_alert_scheduler
    from schedulers.social_media_scheduler import start_social_media_scheduler
    from schedulers.weekly_scheduler import start_weekly_data_scheduler
    from schedulers.monthly_scheduler import start_monthly_data_scheduler
    from schedulers.genetic_scraper_scheduler import start_genetic_scraper_scheduler
    from schedulers.search_scraper_scheduler import start_search_scraper_scheduler

    start_breeding_recommendation_scheduler()
    start_competitor_scheduler()
    start_alert_detail_scheduler()
    start_alert_scheduler()
    start_social_media_scheduler()
    start_weekly_data_scheduler()
    start_monthly_data_scheduler()
    start_genetic_scraper_scheduler()
    start_search_scraper_scheduler()
