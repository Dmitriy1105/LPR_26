"""GEN-010.9 canonical communication renderer.

Consumes only observable event projections and organization metadata. It never receives
scenario Ground Truth, authority grants, or hidden decision outcomes. Calls are rendered
as record summaries (not fabricated transcripts) because speaker-turn annotations do not
exist in the canonical scenario contract.
"""
from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

CHANNELS = {
    "request_information": ("email", 4),
    "delegate": ("email", 4),
    "complete_task": ("call", 2),
    "review": ("meeting", 1),
    "recommend": ("email", 4),
    "object": ("email", 4),
    "revise": ("call", 2),
    "unit_approval": ("meeting", 1),
    "approve": ("meeting", 1),
    "reject": ("meeting", 1),
    "close": ("meeting", 1),
}
ROLE_LABELS = {
    "director": "директор",
    "head_of_sales": "руководитель продаж",
    "corporate_sales_manager": "менеджер по корпоративным продажам",
    "account_manager": "аккаунт-менеджер",
    "business_development_specialist": "специалист по развитию бизнеса",
    "sales_specialist": "специалист отдела продаж",
    "finance_manager": "руководитель финансового подразделения",
    "finance_specialist": "специалист финансового подразделения",
    "technical_manager": "руководитель технического подразделения",
    "technical_specialist": "технический специалист",
    "procurement_manager": "руководитель закупок",
    "procurement_specialist": "специалист по закупкам",
    "legal_manager": "руководитель юридического подразделения",
    "legal_specialist": "специалист юридического подразделения",
    "project_office_manager": "руководитель проектного офиса",
    "project_office_specialist": "специалист проектного офиса",
    "security_manager": "руководитель службы безопасности",
    "security_specialist": "специалист службы безопасности",
    "information_security_manager": "руководитель информационной безопасности",
    "information_security_specialist": "специалист по информационной безопасности",
}
SUBJECTS = {
    "request_information": ("Исходные сведения по сделке", "Уточнение требований", "Материалы для рассмотрения"),
    "delegate": ("Поручение на профильную проверку", "Передача задачи эксперту", "Проверка требований"),
    "complete_task": ("Результат выполнения поручения", "Итоги выполненной проверки", "Статус экспертной задачи"),
    "review": ("Рассмотрение материалов", "Рабочее обсуждение условий", "Результаты проверки"),
    "recommend": ("Рекомендация по дальнейшим действиям", "Экспертное заключение", "Материалы для согласования"),
    "object": ("Возражение по условиям", "Замечания к предложению", "Вопросы для урегулирования"),
    "revise": ("Доработанный вариант предложения", "Результат корректировки", "Ответ на замечания"),
    "unit_approval": ("Результат согласования подразделения", "Подтверждение профильного согласования", "Решение подразделения"),
    "approve": ("Итоговое решение по сделке", "Подтверждение одобрения", "Результат согласования"),
    "reject": ("Решение об отклонении сделки", "Результат рассмотрения предложения", "Итоговое решение"),
    "close": ("Фиксация закрытия процесса", "Завершение эпизода сделки", "Итоговый статус процесса"),
}
TEMPLATES = {
    "request_information": (
        "Для начала рассмотрения сделки {deal_id} прошу уточнить исходные требования и передать необходимые материалы.",
        "Направляю запрос по сделке {deal_id}. Просьба предоставить исходные сведения, необходимые для передачи вопроса на профильную проверку.",
        "Чтобы участники могли перейти к предметному рассмотрению сделки {deal_id}, необходимо собрать и сверить исходную информацию.",
    ),
    "delegate": (
        "Передаю задачу по сделке {deal_id} на профильную проверку. Прошу изучить материалы в пределах компетенции и вернуть результат ответственному сотруднику.",
        "Назначаю проверку по сделке {deal_id}. Зафиксируйте выявленные вопросы и передайте выводы адресату; это поручение не является итоговым одобрением.",
        "Материалы по сделке {deal_id} направлены для экспертной оценки. Следующий шаг — оформить результат проверки и вернуть его инициатору поручения.",
    ),
    "complete_task": (
        "В записи звонка по сделке {deal_id} зафиксировано выполнение порученной проверки. Результат передан для дальнейшего рассмотрения.",
        "Сводка звонка по сделке {deal_id}: исполнитель сообщил о завершении назначенной работы и передаче её результата ответственному участнику.",
        "По звонку зафиксировано, что задача по сделке {deal_id} выполнена; запись отражает статус поручения, а не дословную стенограмму разговора.",
    ),
    "review": (
        "В протоколе встречи по сделке {deal_id} зафиксировано рассмотрение представленных материалов. Выявленные вопросы переданы участникам для оценки.",
        "Рабочая встреча по сделке {deal_id} была посвящена рассмотрению материалов и результатов проверки. Запись фиксирует предмет обсуждения, а не окончательное решение.",
        "В протокол внесено рассмотрение условий сделки {deal_id}; дальнейшие действия определяются результатами последующих согласований.",
    ),
    "recommend": (
        "Направляю рекомендацию по сделке {deal_id} для рассмотрения уполномоченным лицом. Экспертная оценка сама по себе не заменяет итоговое решение.",
        "По результатам профильной оценки предлагаю передать сделку {deal_id} на следующий этап. Окончательное решение остаётся за уполномоченным согласующим.",
        "Подготовлена рекомендация по дальнейшим действиям в рамках сделки {deal_id}; прошу учесть её при последующем рассмотрении.",
    ),
    "object": (
        "Фиксирую возражение по текущим условиям сделки {deal_id}. До продолжения рассмотрения необходимо учесть замечания и урегулировать обозначенные вопросы.",
        "По сделке {deal_id} заявлено возражение. Прошу рассмотреть замечания и подготовить ответ либо скорректированный вариант предложения.",
        "Направляю замечания к текущему варианту сделки {deal_id}. Считаю необходимым вернуться к условиям до принятия дальнейшего решения.",
    ),
    "revise": (
        "В записи звонка по сделке {deal_id} отражена передача доработанного варианта в ответ на ранее заявленные замечания.",
        "Сводка звонка по сделке {deal_id}: обсуждалась корректировка предложения и передача обновлённых материалов на повторное рассмотрение.",
        "По звонку зафиксирована доработка условий сделки {deal_id}. Эта запись отражает передачу обновлённого варианта, а не содержание разговора дословно.",
    ),
    "unit_approval": (
        "В протоколе встречи зафиксировано согласование по сделке {deal_id} в рамках указанного подразделения. Оно не заменяет итоговое решение по сделке.",
        "Подразделение оформило профильное согласование по сделке {deal_id}. Запись относится только к указанной области ответственности.",
        "Встреча зафиксировала результат согласования подразделения по сделке {deal_id}; дальнейший процесс продолжается в соответствии с установленными полномочиями.",
    ),
    "approve": (
        "В протоколе зафиксировано итоговое одобрение сделки {deal_id} уполномоченным участником.",
        "По итогам рассмотрения оформлено решение об одобрении сделки {deal_id}. Запись отражает тип события в журнале.",
        "Встреча завершилась фиксацией одобрения сделки {deal_id}; данное событие относится к итоговому решению.",
    ),
    "reject": (
        "В протоколе зафиксировано отклонение сделки {deal_id}. Событие отражает отрицательный результат рассмотрения.",
        "По итогам рассмотрения оформлено решение об отклонении сделки {deal_id}.",
        "В журнале встречи зафиксировано отклонение предложения по сделке {deal_id}.",
    ),
    "close": (
        "В протоколе зафиксировано закрытие эпизода сделки {deal_id}. Запись подтверждает завершение процесса, но не раскрывает основание итогового статуса.",
        "Эпизод по сделке {deal_id} отмечен как закрытый. В этой коммуникации фиксируется факт завершения, без дополнительной интерпретации результата.",
        "В журнал внесено закрытие процесса по сделке {deal_id}; запись фиксирует завершение эпизода без вывода о его итоговом основании.",
    ),
}


# Additional event-faithful paraphrases; choices are combined independently with
# stable openers/closers to avoid the low-entropy three-template corpus.
EXTRA_TEMPLATES = {
    "request_information": (
        "Прошу дополнить карточку сделки {deal_id} исходными данными, без которых профильное рассмотрение пока нельзя считать подготовленным.",
        "Для передачи сделки {deal_id} ответственным специалистам требуется уточнить исходные параметры и комплект материалов.",
        "По сделке {deal_id} необходимо собрать сведения, на которые смогут опираться участники последующей проверки.",
        "Прошу подтвердить исходные условия сделки {deal_id} и направить материалы для дальнейшей работы.",
        "На текущем этапе по сделке {deal_id} запрашиваются исходные сведения; после их получения вопрос можно передать на проверку.",
        "Для корректной организации рассмотрения сделки {deal_id} прошу предоставить недостающую исходную информацию.",
    ),
    "delegate": (
        "Прошу выполнить профильную проверку материалов по сделке {deal_id} и зафиксировать результат в рамках поручения.",
        "Следующий этап по сделке {deal_id} передаётся на экспертную оценку; прошу вернуть выводы и замечания.",
        "Назначаю ответственному специалисту проверку по сделке {deal_id}; область работы ограничена профильными вопросами.",
        "Прошу рассмотреть материалы сделки {deal_id} с позиции вашей функции и передать заключение инициатору поручения.",
        "Для продолжения процесса требуется экспертная проверка сделки {deal_id}; зафиксируйте результат без принятия итогового решения.",
        "Материалы сделки {deal_id} передаются адресату для выполнения назначенной проверки и обратной связи.",
    ),
    "complete_task": (
        "Исполнитель завершил порученную проверку по сделке {deal_id}; запись звонка фиксирует передачу результата ответственному участнику.",
        "В сводке телефонного взаимодействия отмечено выполнение назначенной задачи по сделке {deal_id}.",
        "Звонок зарегистрирован как подтверждение завершения порученной работы по сделке {deal_id}; дословная речь не реконструируется.",
        "По результатам телефонного контакта отражён статус задачи: проверка по сделке {deal_id} выполнена.",
        "Запись звонка содержит отметку о завершении профильной проверки по сделке {deal_id} и передаче результата.",
        "В карточке звонка сохранено сообщение о выполнении поручения по сделке {deal_id}; это краткая сводка события.",
    ),
    "review": (
        "Участники рассмотрели материалы сделки {deal_id}; протокол сохраняет предмет обсуждения и выявленные вопросы.",
        "Встреча посвящена проверке представленных условий сделки {deal_id}; запись не трактуется как формальное одобрение.",
        "В ходе рабочего рассмотрения сделки {deal_id} участники сверили материалы и результаты профильной проверки.",
        "Протокол отражает этап рассмотрения сделки {deal_id} и вопросы, вынесенные на обсуждение.",
        "По сделке {deal_id} проведено рабочее рассмотрение; зафиксированный этап предшествует отдельному решению.",
        "Встреча зарегистрирована для документирования рассмотрения условий и материалов сделки {deal_id}.",
    ),
    "recommend": (
        "Передаю экспертный вывод по сделке {deal_id}; он предназначен для рассмотрения лицом, обладающим итоговыми полномочиями.",
        "Сформирована рекомендация по дальнейшему движению сделки {deal_id}; прошу учесть её при принятии отдельного решения.",
        "По результатам профильной оценки предлагается продолжить рассмотрение сделки {deal_id} в установленном порядке.",
        "Направляю заключение по сделке {deal_id}. Оно выражает рекомендацию автора и не заменяет решение согласующего.",
        "Материалы по сделке {deal_id} могут быть переданы на следующий этап с учётом изложенной экспертной позиции.",
        "Прошу уполномоченного участника рассмотреть рекомендацию по сделке {deal_id} и зафиксировать собственное решение.",
    ),
    "object": (
        "Текущая редакция условий сделки {deal_id} вызывает возражение; замечания следует рассмотреть до продолжения согласования.",
        "Не поддерживаю представленный вариант сделки {deal_id} без дополнительной проработки обозначенных вопросов.",
        "По сделке {deal_id} направлены возражения к текущему предложению; требуется реакция на замечания.",
        "Считаю необходимым приостановить переход к следующему решению по сделке {deal_id} до рассмотрения возражения.",
        "Прошу вернуться к условиям сделки {deal_id}: в текущем варианте остаются вопросы, зафиксированные как возражения.",
        "Настоящая запись отражает несогласие с текущими условиями сделки {deal_id} и необходимость их повторного рассмотрения.",
    ),
    "revise": (
        "В телефонной сводке отражена передача изменённого предложения по сделке {deal_id} после получения замечаний.",
        "По сделке {deal_id} зарегистрирован звонок, связанный с корректировкой ранее представленных условий.",
        "Запись звонка фиксирует, что инициатор передал обновлённые материалы для повторного рассмотрения сделки {deal_id}.",
        "В ходе телефонного взаимодействия отмечена доработка предложения по сделке {deal_id}; содержание звонка не приводится дословно.",
        "Телефонная запись отражает этап внесения изменений в материалы сделки {deal_id} в ответ на замечания.",
        "По результатам звонка сохранена отметка о повторной подаче скорректированного варианта сделки {deal_id}.",
    ),
    "unit_approval": (
        "Зафиксировано профильное согласование сделки {deal_id} в рамках указанной области ответственности подразделения.",
        "Результат встречи отражает согласование на уровне подразделения и не означает автоматически итоговое одобрение сделки {deal_id}.",
        "В рамках сделки {deal_id} оформлено решение подразделения по его направлению; остальные полномочия сохраняются отдельно.",
        "Протокол содержит отметку о прохождении одного из подразделенческих этапов согласования сделки {deal_id}.",
        "Согласование подразделения по сделке {deal_id} отражено как отдельное событие в общей последовательности решения.",
        "Встреча документирует профильное согласование сделки {deal_id} в пределах компетенции соответствующего подразделения.",
    ),
    "approve": (
        "Уполномоченным участником зафиксировано одобрение сделки {deal_id}; событие отражает итоговый тип решения.",
        "Результат рассмотрения сделки {deal_id} оформлен как одобрение в журнале процесса.",
        "В протокол внесено итоговое согласование сделки {deal_id} лицом, ответственным за финальное решение.",
        "По сделке {deal_id} зарегистрировано положительное итоговое решение; основание и полномочие проверяются отдельными данными.",
        "Настоящая запись документирует факт одобрения сделки {deal_id} в рамках завершающего этапа рассмотрения.",
        "Итоговый этап по сделке {deal_id} завершён фиксацией одобрения уполномоченного участника.",
    ),
    "reject": (
        "Уполномоченным участником зафиксировано отклонение сделки {deal_id}; это событие отражает итоговый тип решения.",
        "Результат рассмотрения сделки {deal_id} зарегистрирован как отклонение предложения.",
        "В протокол внесено отрицательное итоговое решение по сделке {deal_id}.",
        "По сделке {deal_id} оформлено решение об отказе в согласовании представленного варианта.",
        "Настоящая запись документирует факт отклонения сделки {deal_id} на завершающем этапе рассмотрения.",
        "Итоговое рассмотрение сделки {deal_id} завершилось фиксацией отклонения уполномоченным участником.",
    ),
    "close": (
        "Эпизод сделки {deal_id} закрыт; запись не раскрывает и не переопределяет основание итогового статуса.",
        "В истории сделки {deal_id} отмечено закрытие текущего процесса без дополнительного вывода о результате решения.",
        "Регистрация закрытия завершает хронологию данного эпизода сделки {deal_id}; детали результата хранятся в отдельном поле.",
        "По сделке {deal_id} зафиксирован факт закрытия эпизода, при этом текст не интерпретирует итоговое решение.",
        "Настоящая запись завершает последовательность событий по сделке {deal_id}, не раскрывая скрытые оценочные поля.",
        "В журнале отражено закрытие эпизода сделки {deal_id}; текст ограничен наблюдаемым фактом завершения.",
    ),
}

OPENERS = (
    "В рамках сопровождения сделки {deal_id} фиксирую следующее.",
    "Для сохранения истории взаимодействия по сделке {deal_id} внесена запись.",
    "В журнале коммуникаций по сделке {deal_id} отражено следующее событие.",
    "Настоящая запись относится к текущему этапу сделки {deal_id}.",
    "В рабочем контуре согласования сделки {deal_id} отмечено следующее.",
    "По текущему эпизоду сделки {deal_id} сохранена информация о взаимодействии.",
    "В карточке сделки {deal_id} документируется очередной шаг процесса.",
    "Для участников процесса по сделке {deal_id} зафиксирована следующая информация.",
)

CLOSERS = (
    "Запись сохраняет связь с исходным событием и его участниками.",
    "Формулировка ограничена наблюдаемым содержанием события и не добавляет неподтверждённых обстоятельств.",
    "Эта коммуникация дополняет хронологию процесса без изменения исходного события.",
    "Сведения относятся только к указанному этапу и его зафиксированным участникам.",
    "Источник и временная привязка сохранены в структурированных полях записи.",
    "Текст не заменяет отдельные данные о полномочиях и формальном основании решения.",
    "Запись предназначена для последующего просмотра истории процесса.",
    "Содержание не выходит за пределы сведений, доступных в наблюдаемом событии.",
)


def _choice(seed: int, event_id: str, key: str, options: tuple[str, ...]) -> str:
    digest = hashlib.sha256(f"{seed}|{event_id}|{key}".encode("utf-8")).digest()
    return options[int.from_bytes(digest[:8], "big") % len(options)]


def _role_index(organizations: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    result = {}
    for org in organizations:
        roles = {r["contact_id"]: r["role_code"] for r in org["role_assignments"]}
        result[org["organization_id"]] = roles
    return result


def render_communications(observable_events: list[dict[str, Any]],
                          organizations: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    """Render communications from observable projections only; no Ground Truth argument."""
    role_by_org = _role_index(organizations)
    output = []
    seen = set()
    for event in observable_events:
        event_type = event["event_type"]
        if event_type not in CHANNELS:
            raise ValueError("unsupported event type: " + str(event_type))
        event_id = event["event_id"]
        if event_id in seen:
            raise ValueError("duplicate source event: " + event_id)
        seen.add(event_id)
        oid = event["organization_id"]
        roles = role_by_org.get(oid)
        if roles is None:
            raise ValueError("unknown organization for event " + event_id)
        author = event["actor_contact_id"]
        target = event.get("target_contact_id")
        if author not in roles:
            raise ValueError("unknown author for event " + event_id)
        if target is not None and target not in roles:
            raise ValueError("unknown addressee for event " + event_id)

        channel, type_id = CHANNELS[event_type]
        subject = _choice(seed, event_id, "subject", SUBJECTS[event_type])
        body_options = TEMPLATES[event_type] + EXTRA_TEMPLATES[event_type]
        opener = _choice(seed, event_id, "opener", OPENERS).format(deal_id=event["deal_id"])
        main = _choice(seed, event_id, "body", body_options).format(deal_id=event["deal_id"])
        closer = _choice(seed, event_id, "closer", CLOSERS)
        body = opener + " " + main + " " + closer
        note = event.get("context_note")
        if note:
            body += " Контекст события: " + note.rstrip(". ") + "."
        if event_type == "unit_approval":
            body += " Область согласования: " + str(event.get("decision_scope") or "не указана") + "."
        actor_role = roles[author]
        target_role = roles.get(target) if target else None
        author_label = ROLE_LABELS.get(actor_role, actor_role)
        addressee_label = ROLE_LABELS.get(target_role, target_role) if target_role else None
        participant_ids = [author] + ([target] if target and target != author else [])
        output.append({
            "activity_id": "COMM:" + event_id,
            "source_event_id": event_id,
            "source_ref": event["source_ref"],
            "deal_id": event["deal_id"],
            "organization_id": oid,
            "event_type": event_type,
            "decision_scope": event.get("decision_scope"),
            "occurred_at": event["occurred_at"],
            "channel": channel,
            "type_id": type_id,
            "subject": subject,
            "body": body,
            "author_contact_id": author,
            "author_role_code": actor_role,
            "author_role_label": author_label,
            "participant_contact_ids": participant_ids,
            "addressee_contact_ids": [target] if target else [],
            "addressee_role_label": addressee_label,
            "speaker_contact_id": None,
            "speaker_status": "unknown_no_turn_annotation",
            "text_status": "ready",
            "context_note_included": bool(note),
            "missing_fields": list(event.get("missing_fields", [])),
            "synthetic": True,
            "renderer_version": "1.0.0",
        })
    return output


def validate_rendered_communications(observable_events: list[dict[str, Any]],
                                     communications: list[dict[str, Any]]) -> dict[str, Any]:
    errors = []
    event_by_id = {e["event_id"]: e for e in observable_events}
    comm_by_id = {}
    forbidden_fields = {"authority_grant_ref", "authority_grant_refs", "decision_outcome",
                        "ground_truth", "decision_maker_contact_id", "executor_contact_id"}
    semantic_markers = {
        "request_information": ("запрос", "исходн", "прошу", "сведен"),
        "delegate": ("провер", "поруч", "эксперт", "назнач"),
        "complete_task": ("заверш", "выполн", "провер"),
        "review": ("рассмотр", "встреч", "обсужден"),
        "recommend": ("рекомендац", "эксперт", "заключ"),
        "object": ("возраж", "замечан", "несоглас"),
        "revise": ("доработ", "коррект", "обнов", "измен"),
        "unit_approval": ("согласован",),
        "approve": ("одобр",),
        "reject": ("отклон", "отказ", "отрицательн"),
        "close": ("закрыт", "закрыти"),
    }
    for item in communications:
        cid = item["source_event_id"]
        if cid in comm_by_id:
            errors.append("duplicate communication source " + cid)
        comm_by_id[cid] = item
        event = event_by_id.get(cid)
        if event is None:
            errors.append("orphan communication " + cid)
            continue
        if forbidden_fields.intersection(item):
            errors.append("hidden truth field exposed in communication " + cid)
        if item["author_contact_id"] != event["actor_contact_id"]:
            errors.append("author attribution mismatch " + cid)
        expected_participants = [event["actor_contact_id"]]
        target = event.get("target_contact_id")
        if target and target != event["actor_contact_id"]:
            expected_participants.append(target)
        if item["participant_contact_ids"] != expected_participants:
            errors.append("participant attribution mismatch " + cid)
        if item["addressee_contact_ids"] != ([target] if target else []):
            errors.append("addressee attribution mismatch " + cid)
        if item["decision_scope"] != event.get("decision_scope"):
            errors.append("decision scope projection mismatch " + cid)
        if item["occurred_at"] != event["occurred_at"] or item["source_ref"] != event["source_ref"]:
            errors.append("source chronology/provenance mismatch " + cid)
        if item["missing_fields"] != event["missing_fields"]:
            errors.append("missingness projection mismatch " + cid)
        if item["context_note_included"] != bool(event.get("context_note")):
            errors.append("context note visibility mismatch " + cid)
        if not item["body"].strip() or len(item["body"].split()) < 8:
            errors.append("insufficient body text " + cid)
        body_lower = item["body"].lower()
        if not any(marker in body_lower for marker in semantic_markers[event["event_type"]]):
            errors.append("event/text semantic marker mismatch " + cid)
        if event["event_type"] == "approve" and any(x in body_lower for x in ("отклон", "отказ")):
            errors.append("approval text contradicts event type " + cid)
        if event["event_type"] == "reject" and "одобр" in body_lower:
            errors.append("rejection text contradicts event type " + cid)
        if item["speaker_contact_id"] is not None or item["speaker_status"] != "unknown_no_turn_annotation":
            errors.append("speaker identity invented without turn annotation " + cid)
        if event["event_type"] == "close" and any(x in item["body"].lower() for x in ("одобр", "отклон", "approved", "rejected")):
            errors.append("close text leaks hidden outcome " + cid)
    expected_ids = set(event_by_id)
    if set(comm_by_id) != expected_ids:
        errors.append("communication/source event coverage mismatch")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "observable_events": len(observable_events), "communications": len(communications),
            "unique_source_events": len(comm_by_id)}
