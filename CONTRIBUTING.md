# Contributing to MANDI EAR™

Thank you for your interest in contributing to MANDI EAR™! This document provides guidelines and information for contributors.

## 🌾 Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- Git
- Basic understanding of agricultural markets (helpful but not required)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/mandi-ear.git
   cd mandi-ear
   ```

2. **Set up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start Development Services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Run Tests**
   ```bash
   pytest
   ```

## 📝 Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable and function names

### Testing Requirements
- All new features must include tests
- Property-based tests are preferred for core logic
- Maintain test coverage above 80%
- Tests must pass before submitting PR

### Commit Messages
Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `chore`: Maintenance tasks

Examples:
```
feat(voice): add Tamil language support
fix(price): correct MSP calculation for wheat
docs(api): update authentication endpoints
test(ambient-ai): add property tests for conversation analysis
```

## 🏗️ Architecture Guidelines

### Microservices
- Each service should be independent and focused
- Use FastAPI for REST APIs
- Implement proper error handling and logging
- Follow the existing service structure

### Database Design
- Use appropriate database for each use case:
  - PostgreSQL: Transactional data
  - MongoDB: Document storage
  - Redis: Caching and sessions
  - InfluxDB: Time-series data

### API Design
- Follow RESTful principles
- Use proper HTTP status codes
- Implement pagination for list endpoints
- Include comprehensive error responses
- Document all endpoints with OpenAPI

## 🧪 Testing Guidelines

### Property-Based Testing
We use Hypothesis for property-based testing. When adding new features:

1. **Identify Properties**: What should always be true?
2. **Write Property Tests**: Test universal properties
3. **Add Unit Tests**: Test specific examples
4. **Integration Tests**: Test end-to-end workflows

Example property test:
```python
from hypothesis import given, strategies as st

@given(
    price=st.floats(min_value=0.01, max_value=10000),
    quantity=st.floats(min_value=0.01, max_value=1000)
)
def test_price_calculation_properties(price, quantity):
    """Property: Total should always equal price * quantity"""
    total = calculate_total(price, quantity)
    assert abs(total - (price * quantity)) < 0.01
```

### Test Categories
- **Property Tests**: Universal correctness properties
- **Unit Tests**: Individual function testing
- **Integration Tests**: Service interaction testing
- **End-to-End Tests**: Complete user workflows

## 🌍 Internationalization

### Adding New Languages
1. Add language code to supported languages list
2. Create translation files in `locales/`
3. Update voice processing models
4. Add language-specific tests
5. Update documentation

### Translation Guidelines
- Use professional agricultural terminology
- Consider regional variations
- Test with native speakers when possible
- Maintain consistency across services

## 📊 Performance Guidelines

### Optimization Priorities
1. **Response Time**: API responses < 200ms
2. **Throughput**: Handle 1000+ concurrent users
3. **Memory Usage**: Efficient memory management
4. **Database Queries**: Optimize for performance
5. **Caching**: Implement appropriate caching strategies

### Monitoring
- Add metrics for new features
- Include performance benchmarks
- Monitor resource usage
- Set up alerts for critical paths

## 🔒 Security Guidelines

### Data Protection
- Never commit sensitive data
- Use environment variables for secrets
- Implement proper authentication
- Validate all inputs
- Follow OWASP guidelines

### API Security
- Implement rate limiting
- Use HTTPS in production
- Validate request payloads
- Implement proper CORS policies
- Log security events

## 📋 Pull Request Process

### Before Submitting
1. **Update Documentation**: Update relevant docs
2. **Add Tests**: Ensure adequate test coverage
3. **Run Tests**: All tests must pass
4. **Check Style**: Follow code style guidelines
5. **Update Changelog**: Add entry to CHANGELOG.md

### PR Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Property tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added and passing
```

### Review Process
1. **Automated Checks**: CI/CD pipeline runs
2. **Code Review**: Maintainer reviews code
3. **Testing**: Reviewer tests functionality
4. **Approval**: PR approved and merged

## 🐛 Bug Reports

### Before Reporting
1. Check existing issues
2. Update to latest version
3. Reproduce the bug
4. Gather relevant information

### Bug Report Template
```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- MANDI EAR Version: [e.g., 1.2.3]

## Additional Context
Any other relevant information
```

## 💡 Feature Requests

### Before Requesting
1. Check existing feature requests
2. Consider if it fits the project scope
3. Think about implementation complexity
4. Consider impact on existing users

### Feature Request Template
```markdown
## Feature Description
Clear description of the proposed feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should this feature work?

## Alternatives Considered
Other approaches you've considered

## Additional Context
Any other relevant information
```

## 📚 Documentation

### Types of Documentation
- **API Documentation**: OpenAPI/Swagger specs
- **User Guides**: How to use features
- **Developer Docs**: Technical implementation
- **Architecture Docs**: System design
- **Deployment Guides**: Setup and deployment

### Documentation Standards
- Write clear, concise explanations
- Include code examples
- Keep documentation up-to-date
- Use proper markdown formatting
- Include diagrams where helpful

## 🎯 Areas for Contribution

### High Priority
- **Language Support**: Add new Indian languages
- **Accessibility**: Improve accessibility features
- **Performance**: Optimize critical paths
- **Testing**: Increase test coverage
- **Documentation**: Improve user guides

### Medium Priority
- **UI/UX**: Enhance user interface
- **Analytics**: Add new metrics and insights
- **Integration**: Connect with external APIs
- **Mobile**: Improve mobile experience
- **Offline**: Enhance offline capabilities

### Good First Issues
Look for issues labeled `good-first-issue` or `help-wanted` for beginner-friendly contributions.

## 🤝 Community

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussions
- **Email**: technical@mandiear.com

### Getting Help
- Check existing documentation
- Search GitHub issues
- Ask in GitHub Discussions
- Contact maintainers

## 🏆 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Annual contributor highlights
- Special recognition for significant contributions

Thank you for contributing to MANDI EAR™! Together, we're building technology that empowers farmers and transforms agricultural markets. 🌾