# Release Process

This document describes the release process for LUCA NRW Scraper, ensuring consistent, professional, and reliable releases.

## 🎯 Release Philosophy

- **Semantic Versioning**: We follow [SemVer 2.0.0](https://semver.org/)
- **Regular Releases**: Minor releases every 4-6 weeks, patches as needed
- **Quality First**: All releases are tested and documented
- **User Focus**: Release notes written for users, not just developers

## 📋 Version Numbering

### Format: `MAJOR.MINOR.PATCH`

- **MAJOR** (X.0.0): Breaking changes, major architecture changes
- **MINOR** (x.X.0): New features, enhancements, non-breaking changes
- **PATCH** (x.x.X): Bug fixes, security patches, minor improvements

### Examples

- `2.4.0` → `2.4.1`: Bug fix (patch)
- `2.4.1` → `2.5.0`: New feature (minor)
- `2.5.0` → `3.0.0`: Breaking change (major)

### When to Increment

#### MAJOR (Breaking Changes)
- API changes that break existing integrations
- Database schema changes requiring migrations with data loss
- Removal of deprecated features
- Configuration format changes
- Minimum requirement changes (Python, Django version)

#### MINOR (New Features)
- New features added
- New API endpoints
- Enhancements to existing features
- Performance improvements
- New configuration options (backward compatible)
- Deprecation warnings (removal in next major)

#### PATCH (Bug Fixes)
- Bug fixes
- Security patches
- Documentation updates
- Minor UI improvements
- Performance optimizations (no API changes)
- Dependency updates (security)

## 🔄 Release Workflow

### 1. Pre-Release (1 week before)

#### 1.1. Update VERSION File
```bash
# Update VERSION file with new version number
echo "2.5.0" > VERSION
git add VERSION
git commit -m "Bump version to 2.5.0"
```

#### 1.2. Update CHANGELOG.md
```markdown
## [2.5.0] - 2026-02-15

### Added
- New feature X
- Enhancement Y

### Changed
- Improved Z

### Fixed
- Bug fix A
- Security patch B

### Security
- [Details of security fixes if any]
```

#### 1.3. Create Release Notes
```bash
# Copy template and customize
cp RELEASE_NOTES.md releases/RELEASE_NOTES_v2.5.0.md

# Edit with version-specific information
nano releases/RELEASE_NOTES_v2.5.0.md
```

**Release Notes Template**:
```markdown
# Release Notes - LUCA NRW Scraper v2.5.0

**Release Date**: February 15, 2026

## 🎉 What's New
[User-facing new features]

## 📊 Key Improvements
[Important improvements]

## ⚠️ Breaking Changes
[If any - with migration guide]

## 🚀 Upgrade Guide
[Step-by-step upgrade instructions]

## 📖 Documentation Updates
[New or updated docs]

## 🔐 Security Notes
[Security improvements]

## 🐛 Known Issues
[Known issues and workarounds]
```

#### 1.4. Run Full Test Suite
```bash
# Run all tests
cd telis_recruitment
python manage.py test

# Run security checks
python manage.py check --deploy
bandit -r .

# Test all configuration profiles
cp configs/production.env .env
python manage.py check
cp configs/high-volume.env .env
python manage.py check
cp configs/debug.env .env
python manage.py check

# Test scraper
python ../scriptname.py --once --industry recruiter --qpi 2
```

#### 1.5. Update Documentation
```bash
# Update version references in docs
grep -r "2.4.0" docs/ README.md
# Replace with new version

# Verify all links work
# Update screenshots if UI changed
# Review all documentation for accuracy
```

### 2. Release Day

#### 2.1. Create Git Tag
```bash
# Ensure you're on main branch and up to date
git checkout main
git pull origin main

# Create annotated tag
git tag -a v2.5.0 -m "Release v2.5.0

New Features:
- Feature X
- Feature Y

Bug Fixes:
- Fix A
- Fix B

See RELEASE_NOTES.md for full details"

# Push tag to GitHub
git push origin v2.5.0
```

#### 2.2. Create GitHub Release

1. Go to GitHub repository → Releases → "Draft a new release"
2. Select the tag you just created (v2.5.0)
3. Release title: `v2.5.0 - [Short Description]`
   - Example: `v2.5.0 - Enhanced Analytics & Performance`
4. Copy content from RELEASE_NOTES_v2.5.0.md to release description
5. Attach any release artifacts (if applicable)
6. Check "Set as the latest release"
7. Publish release

#### 2.3. Build and Test Docker Image
```bash
# Build with version tag
docker build -t luca-nrw-scraper:2.5.0 .
docker build -t luca-nrw-scraper:latest .

# Test image
docker run -it --rm luca-nrw-scraper:2.5.0 python manage.py check

# Push to registry (if applicable)
docker push luca-nrw-scraper:2.5.0
docker push luca-nrw-scraper:latest
```

#### 2.4. Update Production Deployments

**Staged Rollout (Recommended)**:

1. **Staging Environment** (Day 1):
   ```bash
   # Deploy to staging
   # Monitor for 24 hours
   # Check logs for errors
   ```

2. **Canary Deployment** (Day 2-3):
   ```bash
   # Deploy to 10% of production
   # Monitor metrics
   # Compare with old version
   ```

3. **Full Production** (Day 4):
   ```bash
   # Deploy to all production
   # Monitor closely for first 24 hours
   ```

**Quick Rollout (Small Changes)**:
```bash
# For patch releases or minor updates
# Deploy directly to production
# Monitor closely
```

### 3. Post-Release (Within 1 week)

#### 3.1. Monitor Production
- [ ] Check error rates
- [ ] Review performance metrics
- [ ] Monitor user feedback
- [ ] Check support requests

#### 3.2. Update Documentation Site
- [ ] Update online documentation
- [ ] Post release announcement
- [ ] Update API documentation if changed

#### 3.3. Announce Release
- [ ] GitHub Discussions (if enabled)
- [ ] Internal team notification
- [ ] Customer notification (if applicable)
- [ ] Social media (if applicable)

#### 3.4. Start Next Development Cycle
```bash
# Create development branch for next version
git checkout -b dev/v2.6.0

# Update CHANGELOG.md with [Unreleased] section
# Begin planning next release
```

## 🔧 Release Checklist Template

### Pre-Release
- [ ] VERSION file updated
- [ ] CHANGELOG.md updated
- [ ] RELEASE_NOTES.md created
- [ ] All tests passing
- [ ] Security checks completed
- [ ] Documentation updated
- [ ] Breaking changes documented
- [ ] Migration guide written (if needed)
- [ ] Configuration profiles tested
- [ ] Docker build tested

### Release Day
- [ ] Git tag created and pushed
- [ ] GitHub release published
- [ ] Release notes published
- [ ] Docker images built and pushed
- [ ] Staging deployment completed
- [ ] Staging verification passed

### Post-Release
- [ ] Production deployment completed
- [ ] Production monitoring active
- [ ] No critical errors detected
- [ ] User notifications sent
- [ ] Documentation site updated
- [ ] Next version planning started

## 🚨 Hotfix Process

For critical bugs or security issues:

### 1. Create Hotfix Branch
```bash
git checkout main
git pull origin main
git checkout -b hotfix/v2.5.1
```

### 2. Fix the Issue
```bash
# Make minimal changes to fix the issue
# Test thoroughly
git add .
git commit -m "Fix critical security vulnerability in authentication"
```

### 3. Update Version and Changelog
```bash
echo "2.5.1" > VERSION

# Update CHANGELOG.md
## [2.5.1] - 2026-02-20

### Security
- Fixed critical authentication vulnerability (CVE-YYYY-XXXX)

### Fixed
- Fixed crash when processing certain lead types
```

### 4. Fast-Track Release
```bash
# Merge to main
git checkout main
git merge hotfix/v2.5.1

# Tag and release
git tag -a v2.5.1 -m "Hotfix v2.5.1 - Critical security patch"
git push origin main
git push origin v2.5.1

# Create GitHub release
# Deploy to production ASAP
```

### 5. Post-Hotfix
```bash
# Merge back to development branch
git checkout dev/v2.6.0
git merge main

# Delete hotfix branch
git branch -d hotfix/v2.5.1
```

## 📊 Release Metrics

Track these metrics for each release:

- **Release frequency**: Target 1 minor release per 4-6 weeks
- **Time to deploy**: From tag to production
- **Rollback rate**: % of releases requiring rollback
- **Hotfix frequency**: Hotfixes per minor release
- **Time to hotfix**: From issue discovery to fix deployed

## 🎯 Quality Gates

Before any release can be published:

1. **All Tests Pass**: Unit, integration, end-to-end
2. **Security Scan Clean**: No high/critical vulnerabilities
3. **Documentation Complete**: All new features documented
4. **Configuration Tested**: All profiles work
5. **Deployment Verified**: Staging deployment successful
6. **Performance Acceptable**: No regressions
7. **Breaking Changes Justified**: With migration guide

## 🔐 Security Releases

For security-sensitive releases:

1. **Private Development**: Fix in private branch
2. **Limited Disclosure**: Only inform necessary parties
3. **Coordinated Release**: Prepare patches for supported versions
4. **CVE Assignment**: If applicable
5. **Security Advisory**: Publish after fix is available
6. **Expedited Process**: Skip normal waiting periods
7. **Clear Communication**: Security bulletin with details

## 📝 Version Support Policy

- **Current Major Version**: Full support
- **Previous Major Version**: Security patches for 6 months
- **Older Versions**: No support (upgrade recommended)

Example (Current = v3.x):
- v3.x: Full support (features + security)
- v2.x: Security patches only (until 6 months after v3.0.0)
- v1.x: No support (upgrade to v2.x or v3.x)

## 🛠️ Tools and Automation

### Recommended Tools

- **Version Management**: `bump2version` or manual
- **Changelog**: Keep a Changelog format
- **Release Notes**: Custom templates
- **CI/CD**: GitHub Actions (see .github/workflows/)
- **Testing**: Django test suite, pytest
- **Security**: Bandit, Safety

### Automation Opportunities

Future improvements to automate:

1. Version bumping in all files
2. Changelog generation from commits
3. Release note template population
4. Docker image building and pushing
5. Deployment orchestration
6. Notification distribution

## 🔮 Future Improvements

- [ ] Automated release pipeline
- [ ] Canary deployments
- [ ] Feature flags for gradual rollout
- [ ] Automated rollback on error spike
- [ ] Beta/RC releases for early adopters
- [ ] Release preview environment

## 📚 Additional Resources

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Deployment Guide](DEPLOYMENT.md)
- [Security Checklist](SECURITY_CHECKLIST.md)

---

**Questions about the release process?**  
Contact the release manager or open a GitHub Discussion.
