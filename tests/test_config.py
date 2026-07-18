from restaurant_rec.config import Settings, get_settings


def test_settings_load_defaults() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.llm_model == "gemini-flash-latest"
    assert settings.hf_dataset_name == "ManikaSaini/zomato-restaurant-recommendation"
    assert settings.log_level == "INFO"
