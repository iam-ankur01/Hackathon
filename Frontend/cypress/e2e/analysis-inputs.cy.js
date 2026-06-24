const apiUrl = 'http://127.0.0.1:8000'

const openAuthenticatedDashboard = () => {
  const email = `analysis-inputs-${Date.now()}-${Cypress._.random(1000, 9999)}@example.com`
  const password = 'CypressPass123!'

  cy.request('POST', `${apiUrl}/api/auth/signup`, {
    name: 'Input Test Candidate',
    email,
    password,
    role: 'Software Engineer',
    college: 'Test University',
  }).then(({ body }) => {
    cy.visit('/dashboard', {
      onBeforeLoad(win) {
        win.localStorage.setItem('hs_token', body.access_token)
        win.localStorage.setItem('hs_user', JSON.stringify(body.user))
      },
    })
  })
}

describe('Analysis input modes', () => {
  beforeEach(() => {
    openAuthenticatedDashboard()
  })

  it('shows an exact upload error when no file is selected', () => {
    cy.contains('button', 'Analyze Interview').click()
    cy.get('[role="alert"]').within(() => {
      cy.contains('No file selected').should('be.visible')
      cy.contains('Choose or drop an interview audio/video file').should('be.visible')
    })
  })

  it('always shows a clear Start Recording option when Record Audio is selected', () => {
    cy.get('input[type="file"][accept="video/*,audio/*"]').selectFile({
      contents: Cypress.Buffer.from('temporary media selection'),
      fileName: 'temporary.mp3',
      mimeType: 'audio/mpeg',
    }, { force: true })

    cy.contains('button', 'Record Audio').click()
    cy.contains('button', 'Start Recording').should('be.visible')
    cy.contains('Record your interview answer').should('be.visible')
  })

  it('shows niche Zoom-link errors', () => {
    cy.contains('button', 'Zoom Link').click()
    cy.contains('button', 'Analyze Interview').click()
    cy.contains('[role="alert"]', 'Invalid Zoom link').should('be.visible')

    cy.get('input[placeholder*="Zoom cloud recording"]').type('https://example.com/recording')
    cy.contains('button', 'Analyze Interview').click()
    cy.contains('[role="alert"]', 'Not a Zoom recording link').should('be.visible')

    cy.get('input[placeholder*="Zoom cloud recording"]').clear().type('https://acme.zoom.us/rec/share/example')
    cy.contains('button', 'Analyze Interview').click()
    cy.get('[role="alert"]').within(() => {
      cy.contains('Zoom import is not available yet').should('be.visible')
      cy.contains('Download the recording from Zoom').should('be.visible')
    })
  })
})
