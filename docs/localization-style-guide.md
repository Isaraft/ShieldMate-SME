# English, Russian and Kazakh product language

Use concise, professional language for Kazakhstan SME owners and IT generalists. Explain the next action and its evidence. Avoid literal translations, fear-based marketing, claims of comprehensive protection, and unsupported vulnerability claims. Russian uses natural imperative forms; Kazakh uses native sentence structure and polite action instructions. Translations are authored and editorially reviewed during implementation; independent native-speaker review is still required. No native-language certification is claimed.

## Canonical terminology

| English | Русский | Қазақша |
|---|---|---|
| Domain | Домен | Домен |
| Domain ownership verification | Подтверждение управления доменом | Доменге иелік етуді растау |
| Verified domain | Подтверждённый домен | Расталған домен |
| Organization | Организация | Ұйым |
| Workspace | Рабочая область | Жұмыс кеңістігі |
| Limited external assessment | Ограниченная внешняя проверка | Шектеулі сыртқы тексеру |
| Security report | Отчёт о безопасности | Қауіпсіздік туралы есеп |
| Finding | Выявленная проблема | Анықталған мәселе |
| Vulnerability | Уязвимость | Осалдық |
| Technical evidence | Технические подтверждения | Техникалық дәлелдер |
| Observation | Наблюдение | Бақылау нәтижесі |
| Recommended actions | Рекомендуемые действия | Ұсынылатын әрекеттер |
| Remediation task | Задача по устранению проблемы | Мәселені жою тапсырмасы |
| Owner label | Ответственный | Жауапты тұлға |
| Task completed | Задача выполнена | Тапсырма орындалды |
| Resolution confirmed | Устранение подтверждено | Жойылғаны расталды |
| Scan history | История проверок | Тексеру тарихы |
| Risk level | Уровень риска | Тәуекел деңгейі |
| Priority | Приоритет | Басымдық |
| Incomplete assessment | Проверка завершена не полностью | Тексеру толық аяқталмады |
| Inconclusive result | Недостаточно данных для вывода | Қорытынды жасауға дерек жеткіліксіз |
| Synthetic demonstration | Демонстрация на вымышленных данных | Жасанды деректермен көрсетілім |

A finding describes supported evidence of a configuration issue; it is not automatically a proven exploitable vulnerability. Human task completion never changes a technical finding's resolution. Fresh, supported scanner evidence is required. Empty, partial or failed assessments never mean that an organization is secure.

## Catalog and formatting rules

The shared catalogs live in `backend/app/locales/{en,ru,kk}.json`; the frontend imports these exact files. Existing English phrase keys remain compatible; new contextual messages use descriptive keys and named placeholders. `scripts/check-locales.cjs` checks every catalog key, nonempty translation, named interpolation parity, and literal UI references. Backend tests independently check parity. Do not concatenate translated sentence fragments to enforce English word order. Headline composition has whole contextual locale-specific phrases.

Preserve protocol names (DNS, TXT, TLS, HTTP, SPF, DMARC), domain names, identifiers, hashes, canonical enum values, user notes and organization/owner names. Translate controlled labels, never request values. Unknown technical evidence remains exact. Use `kk`, never `kz`, for the language. Unknown saved locale values fall back to English; existing `en`/`ru` choices remain valid. Browser language is used only when no saved preference exists. Only the locale preference is stored in browser storage; sessions remain HttpOnly cookies.

Native selector labels are English / Русский / Қазақша. Switching preserves route and unsent form state. UI dates use Intl with Asia/Almaty and an explicit timezone label; printable evidence uses a consistently labeled UTC timestamp. Numeric presentation may be localized; raw evidence and canonical API values are preserved.

Anton remains the Latin display face. IBM Plex Sans covers UI/body and Russian/Kazakh headings, with explicit Cyrillic-ext ranges. PDFs embed licensed Plex-derived print subsets; source, modification and hashes are recorded beside the fonts. No fonts are fetched at runtime.
