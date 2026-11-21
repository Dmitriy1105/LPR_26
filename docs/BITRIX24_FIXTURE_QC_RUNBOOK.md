# Проверка синтетических REST-данных Bitrix24

Данные для просмотра: `src/data/bitrix24_contract_v1/` (JSON, UTF-8).

- `manifest.json` — методы, число записей, страницы и ограничения;
- `id_mapping.json` — соответствие внутренних и REST ID;
- `companies/`, `contacts/`, `deals/`, `invoices/`, `activities/`, `tasks/` — примеры ответов REST;
- `errors/` — примеры ошибок.

Исходные данные генерации: `src/data/crm.json` и
`src/data/synthetic/bank_ml_v2.json`. Аналитические ручные оценки
не должны экспортироваться в REST-поля.

## Проверка на локальном компьютере

Требуется Node.js 22 и npm.

```bash
node scripts/generate_bitrix24_contract_fixtures.mjs
git diff --exit-code -- src/data/bitrix24_contract_v1
npm test
npm ci
npm run build
```

Команда `git diff --exit-code` завершится с ошибкой, если генератор изменил
сохранённые фикстуры. Это признак несинхронизированных файлов, а не
доказательство несовместимости с Bitrix24.

GitHub Actions: `.github/workflows/bitrix24-fixtures.yml`.
Файлы имитируют *подмножество* классического REST Bitrix24, а не REST 3.0.
Они не подтверждены интеграционным тестом на реальном портале.
