from sqlmodel import Session, select
from typing import Optional, Dict, Any, List
from app.models import GlobalFilter, Source
from app.database import engine


class FilterService:
    """Сервис для управления фильтрами вакансий."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_global_filter(self) -> Optional[GlobalFilter]:
        """Получить глобальный фильтр."""
        return self.session.exec(select(GlobalFilter).limit(1)).first()
    
    def save_global_filter(self, enabled: bool = True, filter_json: Optional[Dict[str, Any]] = None) -> GlobalFilter:
        """Сохранить глобальный фильтр."""
        existing = self.get_global_filter()
        if existing:
            existing.enabled = enabled
            if filter_json is not None:
                existing.filter_json = filter_json
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            gf = GlobalFilter(enabled=enabled, filter_json=filter_json or {})
            self.session.add(gf)
            self.session.commit()
            self.session.refresh(gf)
            return gf
    
    def get_source_filter(self, source_id: str) -> Optional[Source]:
        """Получить фильтр для источника."""
        return self.session.get(Source, source_id)
    
    def save_source_filter(
        self,
        source_id: str,
        name: str,
        enabled: bool = True,
        use_global_filter: bool = True,
        local_filter_json: Optional[Dict[str, Any]] = None,
        config_json: Optional[Dict[str, Any]] = None
    ) -> Source:
        """Сохранить фильтр для источника."""
        existing = self.get_source_filter(source_id)
        if existing:
            existing.name = name
            existing.enabled = enabled
            existing.use_global_filter = use_global_filter
            if local_filter_json is not None:
                existing.local_filter_json = local_filter_json
            if config_json is not None:
                existing.config_json = config_json
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            source = Source(
                id=source_id,
                name=name,
                enabled=enabled,
                use_global_filter=use_global_filter,
                local_filter_json=local_filter_json or {},
                config_json=config_json or {}
            )
            self.session.add(source)
            self.session.commit()
            self.session.refresh(source)
            return source
    
    def get_effective_filter(self, source_id: str) -> Dict[str, Any]:
        """
        Получить эффективный фильтр для источника.
        Если use_global_filter=True,_merge глобальный фильтр с override из local_filter.
        """
        source = self.get_source_filter(source_id)
        global_filter = self.get_global_filter()
        
        if not source or not source.use_global_filter:
            # Используем только локальный фильтр
            return source.local_filter_json if source and source.local_filter_json else {}
        
        if not global_filter or not global_filter.enabled:
            # Глобальный фильтр отключен
            return source.local_filter_json if source and source.local_filter_json else {}
        
        # Merge глобального фильтра с локальным override
        effective = dict(global_filter.filter_json) if global_filter.filter_json else {}
        if source and source.local_filter_json:
            # Локальный фильтр переопределяет глобальный
            effective.update(source.local_filter_json)
        
        return effective
    
    def test_filter(self, vacancy_data: Dict[str, Any], source_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Протестировать фильтр на вакансии.
        Возвращает результат фильтрации.
        """
        from app.services.llm_service import LLMService
        
        effective_filter = self.get_effective_filter(source_id) if source_id else {}
        
        # Hard filters
        result = {
            "passed": True,
            "reason": None,
            "score": 0,
            "remote": vacancy_data.get("remote"),
            "grade": vacancy_data.get("grade_hint"),
        }
        
        # Remote check
        if effective_filter.get("remote_only") and not vacancy_data.get("remote"):
            result["passed"] = False
            result["reason"] = "not_remote"
            return result
        
        # Grade check
        min_grade = effective_filter.get("min_grade", "middle")
        grade_order = {"intern": 0, "junior": 1, "middle": 2, "senior": 3, "lead": 4}
        vacancy_grade = vacancy_data.get("grade_hint", "").lower()
        if vacancy_grade in grade_order:
            min_grade_val = grade_order.get(min_grade.lower(), 2)
            if grade_order[vacancy_grade] < min_grade_val:
                result["passed"] = False
                result["reason"] = f"grade_below_{min_grade}"
                return result
        
        # Keywords check
        primary_keywords = effective_filter.get("primary_keywords", [])
        description = (vacancy_data.get("description_text") or "").lower()
        title = (vacancy_data.get("title") or "").lower()
        text = f"{title} {description}"
        
        if primary_keywords:
            has_keyword = any(kw.lower() in text for kw in primary_keywords)
            if not has_keyword:
                result["passed"] = False
                result["reason"] = "no_primary_keywords"
                return result
        
        # Exclude keywords check
        exclude_keywords = effective_filter.get("exclude_keywords", [])
        if exclude_keywords:
            has_excluded = any(kw.lower() in text for kw in exclude_keywords)
            if has_excluded:
                result["passed"] = False
                result["reason"] = "excluded_keyword"
                return result
        
        # Blacklist check
        blacklist = effective_filter.get("blacklist", {})
        companies = blacklist.get("companies", [])
        company = (vacancy_data.get("company") or "").lower()
        
        for bl_company in companies:
            bl_name = bl_company.get("name", "").lower()
            aliases = [a.lower() for a in bl_company.get("aliases", [])]
            domains = [d.lower() for d in bl_company.get("domains", [])]
            
            if bl_name and bl_name in company:
                result["passed"] = False
                result["reason"] = "blacklisted_company"
                return result
            
            for alias in aliases:
                if alias and alias in company:
                    result["passed"] = False
                    result["reason"] = "blacklisted_company_alias"
                    return result
        
        # LLM classification (optional)
        llm_service = LLMService()
        if llm_service.is_configured():
            try:
                llm_result = llm_service.classify_vacancy(vacancy_data, effective_filter)
                result["score"] = llm_result.get("score", 0)
                result["match_reason"] = llm_result.get("reasons", [])
                if not llm_result.get("match"):
                    result["passed"] = False
                    result["reason"] = "llm_rejected"
            except Exception as e:
                result["llm_error"] = str(e)
        
        return result
    
    def initialize_default_sources(self):
        """Инициализировать источники по умолчанию."""
        default_sources = [
            {"id": "hh", "name": "HH.ru", "enabled": True, "use_global_filter": True},
            {"id": "hirify", "name": "Hirify", "enabled": True, "use_global_filter": True},
            {"id": "telegram_channels", "name": "Telegram Channels", "enabled": True, "use_global_filter": True},
        ]
        
        for src in default_sources:
            self.save_source_filter(
                source_id=src["id"],
                name=src["name"],
                enabled=src["enabled"],
                use_global_filter=src["use_global_filter"]
            )
    
    def initialize_default_global_filter(self):
        """Инициализировать глобальный фильтр по умолчанию."""
        default_filter = {
            "enabled": True,
            "remote_only": True,
            "min_grade": "middle",
            "primary_keywords": [
                "golang", "go", "backend", "back-end", "бэкенд"
            ],
            "secondary_keywords": [
                "kubernetes", "postgresql", "docker", "grpc", "microservices"
            ],
            "exclude_keywords": [
                "junior", "intern", "trainee", "стажер", "джуниор"
            ],
            "allow_full_stack": True,
            "full_stack_backend_focus_min": 0.6,
            "blacklist": {
                "companies": []
            }
        }
        self.save_global_filter(enabled=True, filter_json=default_filter)
