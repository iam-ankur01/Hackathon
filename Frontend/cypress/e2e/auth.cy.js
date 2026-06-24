const uniqueEmail = (prefix) =>
  `${prefix}-${Date.now()}-${Cypress._.random(1000, 9999)}@example.com`
const apiUrl = 'http://127.0.0.1:8000'

describe('HireSight authentication', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
  })

  it('loads the landing page and opens sign in', () => {
    cy.visit('/')
    cy.contains('h1', 'Know exactly where').should('be.visible')
    cy.contains('a', 'Sign in').click()
    cy.location('pathname').should('eq', '/login')
    cy.contains('h1', 'Welcome back').should('be.visible')
  })

  it('creates an account and reaches the dashboard', () => {
    const email = uniqueEmail('signup')

    cy.visit('/login')
    cy.contains('button', 'Sign up free').click()
    cy.contains('h1', 'Create your account').should('be.visible')

    cy.get('input[placeholder="Onkar Kulkarni"]').type('Cypress Candidate')
    cy.get('input[placeholder="you@example.com"]').type(email)
    cy.get('input[type="password"]').type('CypressPass123!')
    cy.get('input[placeholder="SPPU / TCS"]').type('Test University')

    cy.intercept('POST', '**/api/auth/signup').as('signup')
    cy.intercept('PATCH', '**/api/users/me').as('profileUpdate')
    cy.contains('button', 'Create Account').click()

    cy.wait('@signup').its('response.statusCode').should('eq', 200)
    cy.wait('@profileUpdate').its('response.statusCode').should('eq', 200)
    cy.contains('h1', 'Add your profile links').should('be.visible')
    cy.contains('button', 'Skip for now').click()

    cy.location('pathname').should('eq', '/dashboard')
    cy.contains('h1', 'Welcome back, Cypress').should('be.visible')
    cy.window().then((win) => {
      expect(win.localStorage.getItem('hs_token')).to.be.a('string').and.not.be.empty
      expect(win.localStorage.getItem('hs_user')).to.contain(email)
    })
  })

  it('signs in an existing account', () => {
    const email = uniqueEmail('login')
    const password = 'CypressPass123!'

    cy.request('POST', `${apiUrl}/api/auth/signup`, {
      name: 'Login Candidate',
      email,
      password,
      role: 'Software Engineer',
      college: 'Test University',
    }).its('status').should('eq', 200)

    cy.visit('/login')
    cy.get('input[placeholder="you@example.com"]').type(email)
    cy.get('input[type="password"]').type(password)
    cy.intercept('POST', '**/api/auth/login').as('login')
    cy.contains('button', 'Sign In').click()

    cy.wait('@login').its('response.statusCode').should('eq', 200)
    cy.location('pathname').should('eq', '/dashboard')
    cy.contains('h1', 'Welcome back, Login').should('be.visible')
  })
})

