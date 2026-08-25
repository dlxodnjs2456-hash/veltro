# VELTRO

VELTRO 해외선물 모의거래 HTS 백엔드/관리 인프라 저장소입니다.

## Current infrastructure
- Supabase project: `mzjkvakigwtlibwlslhq`
- Edge Function: `trading-api`
- Vercel service: `veltro`

## Backend data
- profiles
- accounts
- instruments
- orders
- fills
- positions
- notices
- messages
- inquiries
- audit_logs

모든 사용자 데이터는 Supabase Auth + RLS 기준으로 분리합니다.
