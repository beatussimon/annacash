# ANNA Security Checklist

## Authentication & Authorization
- [x] Custom User model with proper password hashing
- [x] Session management with secure cookies
- [x] Contextual app-scoped permissions
- [x] Role-based access control (Wakala & Mchezo domains)
- [x] Superuser separate from domain roles

## Financial Transaction Security
- [x] Every transaction attributed to exact user
- [x] Timestamped precisely (UTC with timezone awareness)
- [x] Immutable audit trail
- [x] Soft deletes only (no hard deletion of financial data)
- [x] Financial day locking (closed days read-only)

## Data Protection
- [x] CSRF protection enabled
- [x] XSS protection via Django templates
- [x] SQL injection protection via Django ORM
- [x] Sensitive data in environment variables
- [x] Database connection encryption (configure for production)

## Session Security
- [ ] Set SESSION_COOKIE_SECURE = True (production)
- [ ] Set SESSION_COOKIE_HTTPONLY = True
- [ ] Set SESSION_COOKIE_SAMESITE = 'Lax'
- [ ] Configure session expiry for financial operations

## Production Checklist
- [ ] Change SECRET_KEY from default
- [ ] Set DEBUG = False
- [ ] Configure ALLOWED_HOSTS
- [ ] Use HTTPS only
- [ ] Configure database with strong passwords
- [ ] Set up Redis for session storage
- [ ] Configure email for notifications
- [ ] Set up log aggregation
- [ ] Configure backup strategy
- [ ] Set up monitoring and alerting

## Tanzania Compliance
- [ ] Data residency in Tanzania
- [ ] Swahili language support
- [ ] TZS currency formatting
- [ ] Mobile money network integration
- [ ] Mobile-responsive design for low-bandwidth environments

## Audit Requirements
- [x] All critical actions logged
- [x] User attribution for every action
- [x] IP address tracking
- [x] Old/new value tracking for changes
- [ ] Regular audit log review process
- [ ] Define log retention policy (minimum 7 years for financial data)
