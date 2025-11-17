# CLAUDE.md - AI Assistant Guide

**Last Updated:** 2025-11-17
**Repository:** kangjh3kang-beep/-
**Current State:** Initial/Starter Repository

## Repository Overview

This is a minimal starter repository currently containing only basic scaffolding. As the codebase evolves, this document should be updated to reflect the actual structure, patterns, and conventions used.

### Current Structure

```
/-
├── .git/           # Git repository metadata
├── README.md       # Project README (currently minimal)
└── CLAUDE.md       # This file - AI assistant guidelines
```

## Development Workflow

### Branch Strategy

- **Main Branch:** Not explicitly defined yet (repository is new)
- **Feature Branches:** Use `claude/` prefix for AI-assisted development
  - Format: `claude/claude-md-<session-id>-<unique-id>`
  - Example: `claude/claude-md-mi2ko53oaquij2k8-01BBbVDUEXAiord1D7BLpozy`

### Git Operations

**Committing Changes:**
- Write clear, descriptive commit messages
- Follow conventional commit format when applicable:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `docs:` for documentation updates
  - `refactor:` for code refactoring
  - `test:` for adding tests
  - `chore:` for maintenance tasks

**Pushing Changes:**
- Always use: `git push -u origin <branch-name>`
- Branch names MUST start with `claude/` and include matching session ID
- Retry on network failures with exponential backoff (2s, 4s, 8s, 16s)

**Example Workflow:**
```bash
# Make changes
git add .
git commit -m "feat: add feature description"
git push -u origin claude/claude-md-<session-id>-<unique-id>
```

## Code Conventions

> **Note:** As this is a new repository, conventions should be established as the codebase grows. Update this section when patterns emerge.

### General Guidelines

1. **Code Quality:**
   - Write clean, readable, and maintainable code
   - Add comments for complex logic
   - Follow DRY (Don't Repeat Yourself) principle
   - Use meaningful variable and function names

2. **Security:**
   - Avoid security vulnerabilities (SQL injection, XSS, command injection, etc.)
   - Follow OWASP Top 10 best practices
   - Never commit sensitive data (credentials, API keys, tokens)
   - Use `.gitignore` to exclude sensitive files

3. **Testing:**
   - Write tests for new features
   - Ensure tests pass before committing
   - Aim for good test coverage

4. **Documentation:**
   - Document public APIs and complex functions
   - Keep README.md updated with project information
   - Update CLAUDE.md when patterns or conventions change

## File Organization

> **To Be Defined:** As the project grows, document the directory structure here.

Suggested structure for future development:

```
/-
├── src/            # Source code
├── tests/          # Test files
├── docs/           # Additional documentation
├── config/         # Configuration files
├── scripts/        # Utility scripts
├── .gitignore      # Git ignore patterns
├── README.md       # Project overview
└── CLAUDE.md       # This file
```

## Technology Stack

> **To Be Defined:** Document languages, frameworks, and tools as they are added.

### Current Stack
- Git for version control
- Repository hosted on GitHub

### Future Considerations
When adding technologies, document:
- Language(s) and version(s)
- Framework(s) and version(s)
- Build tools and package managers
- Testing frameworks
- CI/CD tools
- Deployment platforms

## Development Setup

> **To Be Defined:** Document setup instructions when dependencies are added.

### Prerequisites
- Git

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd -

# Additional setup steps will be added as the project grows
```

## Common Tasks

### Creating a New Feature
1. Create a feature branch: `git checkout -b claude/<feature-name>-<session-id>`
2. Implement the feature
3. Test thoroughly
4. Commit with descriptive message
5. Push to remote
6. Create pull request (if applicable)

### Updating Documentation
1. Update relevant documentation files
2. Ensure accuracy and completeness
3. Commit changes: `git commit -m "docs: update <description>"`
4. Push changes

## AI Assistant Best Practices

### When Working on This Repository

1. **Always Check Current State:**
   - Run `git status` to understand current branch and changes
   - Check `git log` to review recent commits
   - Review existing files before making changes

2. **Plan Before Acting:**
   - Use TodoWrite tool for multi-step tasks
   - Break complex tasks into manageable steps
   - Mark tasks as in_progress/completed appropriately

3. **Prefer Editing Over Creating:**
   - Always edit existing files when possible
   - Only create new files when absolutely necessary
   - Check if similar functionality exists before adding new code

4. **Security First:**
   - Never introduce security vulnerabilities
   - Validate and sanitize all inputs
   - Use secure coding practices
   - Review code for security issues before committing

5. **Communication:**
   - Provide clear, concise updates
   - Explain significant changes
   - Ask for clarification when requirements are ambiguous

6. **Tool Usage:**
   - Use specialized tools (Read, Edit, Write) for file operations
   - Avoid bash commands for file manipulation
   - Run independent commands in parallel when possible
   - Use Task tool for complex multi-step explorations

## Repository-Specific Notes

### Current Status (2025-11-17)
- Repository is in initial state
- Only contains README.md and CLAUDE.md
- No production code yet
- Single commit in history

### Next Steps for Development
When starting development, consider:
1. Define the project purpose in README.md
2. Set up appropriate directory structure
3. Add .gitignore with relevant patterns
4. Choose and document technology stack
5. Set up development environment
6. Establish coding standards and style guide
7. Set up testing framework
8. Configure CI/CD if applicable

## Updating This Document

This document should be updated whenever:
- New patterns or conventions are established
- Directory structure changes significantly
- New technologies are added to the stack
- Development workflows are modified
- Important decisions are made that affect development

**Update Process:**
1. Edit CLAUDE.md with new information
2. Update "Last Updated" date at the top
3. Commit: `git commit -m "docs: update CLAUDE.md with <changes>"`
4. Push changes

## Resources

### Git Information
- Remote: `http://local_proxy@127.0.0.1:49677/git/kangjh3kang-beep/-`
- Current Branch: `claude/claude-md-mi2ko53oaquij2k8-01BBbVDUEXAiord1D7BLpozy`

### External Documentation
- Add links to relevant documentation as the project grows
- Include framework documentation
- Link to style guides or coding standards
- Reference architecture decision records (ADRs) if used

---

**Note to AI Assistants:** This document will evolve as the repository grows. Always check the "Last Updated" date and verify information against the current repository state. When in doubt, explore the codebase to understand the current implementation before making assumptions based on this documentation.
