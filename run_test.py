import os
os.environ['FLASK_ENV'] = 'development'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['ADMIN_EMAIL'] = 'admin@jobnest.test'
os.environ['ADMIN_PASSWORD'] = 'Admin@123456'
os.environ['ADMIN_NAME'] = 'Test Admin'

from app import create_app

app = create_app('development')
# Disable CSRF for testing (test client doesn't send tokens)
app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
lines = ['APP OK routes=%d' % len(list(app.url_map.iter_rules()))]
c = app.test_client()

public = ['/', '/jobs', '/companies', '/about', '/contact', '/privacy', '/terms',
          '/auth/login', '/auth/register', '/this-does-not-exist']
for ep in public:
    r = c.get(ep)
    lines.append('%s -> %d' % (ep, r.status_code))

# Register a seeker
r = c.post('/auth/register', data={
    'full_name': 'Test Seeker',
    'email': 'seeker@jobnest.test',
    'phone': '1234567890',
    'password': 'Seeker@123',
    'confirm_password': 'Seeker@123',
    'account_type': 'seeker',
}, follow_redirects=True)
lines.append('register seeker -> %d' % r.status_code)

r = c.post('/auth/login', data={'email': 'seeker@jobnest.test', 'password': 'Seeker@123'},
           follow_redirects=True)
lines.append('login seeker -> %d' % r.status_code)

for ep in ['/seeker/dashboard', '/seeker/profile', '/seeker/resume', '/seeker/education',
           '/seeker/experience', '/seeker/skills', '/seeker/applications', '/seeker/saved-jobs',
           '/seeker/notifications']:
    r = c.get(ep)
    lines.append('%s -> %d' % (ep, r.status_code))

# Add a skill then check profile completion
r = c.post('/seeker/skills', data={'name': 'Python'}, follow_redirects=True)
lines.append('add skill -> %d' % r.status_code)

c.get('/auth/logout')

# Employer
r = c.post('/auth/register', data={
    'full_name': 'Test Employer',
    'email': 'emp@jobnest.test',
    'phone': '1234567890',
    'password': 'Emp@12345',
    'confirm_password': 'Emp@12345',
    'account_type': 'employer',
}, follow_redirects=True)
lines.append('register employer -> %d' % r.status_code)
r = c.post('/auth/login', data={'email': 'emp@jobnest.test', 'password': 'Emp@12345'},
           follow_redirects=True)
lines.append('login employer -> %d' % r.status_code)
for ep in ['/employer/dashboard', '/employer/company', '/employer/post-job', '/employer/my-jobs',
           '/employer/notifications']:
    r = c.get(ep)
    lines.append('%s -> %d' % (ep, r.status_code))
c.get('/auth/logout')

# Admin
r = c.post('/auth/login', data={'email': 'admin@jobnest.test', 'password': 'Admin@123456'},
           follow_redirects=True)
lines.append('login admin -> %d' % r.status_code)
admin_eps = ['/admin/dashboard', '/admin/users', '/admin/companies', '/admin/jobs',
             '/admin/categories', '/admin/applications', '/admin/messages', '/admin/banners',
             '/admin/settings', '/admin/homepage', '/admin/about', '/admin/legal',
             '/admin/audit-logs', '/admin/notifications']
for ep in admin_eps:
    r = c.get(ep)
    lines.append('%s -> %d' % (ep, r.status_code))

# RBAC: ensure clean logout before switching roles so the test is accurate
c.get('/auth/logout')
r = c.post('/auth/login', data={'email': 'seeker@jobnest.test', 'password': 'Seeker@123'}, follow_redirects=True)
lines.append('relogin seeker -> %d' % r.status_code)
r = c.get('/admin/dashboard')
lines.append('seeker->admin (expect 403) -> %d' % r.status_code)
r = c.get('/employer/dashboard')
lines.append('seeker->employer (expect 403) -> %d' % r.status_code)

c.get('/auth/logout')
r = c.post('/auth/login', data={'email': 'emp@jobnest.test', 'password': 'Emp@12345'}, follow_redirects=True)
lines.append('relogin employer -> %d' % r.status_code)
r = c.get('/admin/dashboard')
lines.append('employer->admin (expect 403) -> %d' % r.status_code)
r = c.get('/seeker/dashboard')
lines.append('employer->seeker (expect 403) -> %d' % r.status_code)

lines.append('DONE')

with open('_test.txt', 'w') as f:
    f.write('\n'.join(lines) + '\n')
