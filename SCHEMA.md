# Схема данных

Каждое важное наблюдение рекомендуется хранить отдельной карточкой Markdown или YAML.

## Обязательные поля

```yaml
id: alex.behavior.example
title: Короткое название
category: behavior
status: active
claim_type: direct_observation
confidence: high
period:
  from: YYYY-MM-DD
  to:
summary: Краткое содержание
evidence:
  - source_id: source.example
    locator: ссылка, дата, глава или таймкод
    quote: короткая цитата, если необходима
interpretation: Что наблюдение говорит о публичном образе
humor_use:
  straight: реалистичная стилизация
  exaggerated: карикатурное развитие
related:
  - alex.language.example
tags: []
updated: YYYY-MM-DD
```

## Временная модель

Нельзя считать повадку вечной. У записи указываются период и статус:

- `active` — наблюдается сейчас;
- `historical` — характерно для прошлой эпохи;
- `recurring` — периодически возвращается;
- `uncertain` — данных недостаточно;
- `superseded` — заменено более новым наблюдением.

## Карточка источника

```yaml
id: source.neolurk
title: Алекс Экслер — Неолурк
url: https://neolurk.org/wiki/Алекс_Экслер
source_type: satirical_wiki
reliability: low_for_facts_high_for_meme_history
retrieved: YYYY-MM-DD
notes: Содержит грубую лексику, субъективные оценки и непроверенные утверждения.
```

## Принципы редактирования

- Не превращать повторяемую шутку в биографический факт.
- Не приписывать человеку диагнозы и преступления.
- Сохранять дату наблюдения и точный первоисточник.
- Отделять дословную цитату от пересказа.
- При противоречии хранить обе версии и отмечать расхождение.
- Для внешности хранить привязку к конкретному периоду и изображению.
