/**
 * Property 7: Only PDFs reach the file list
 * Validates: Requirements 1.4
 */
import { describe, it } from 'vitest'
import * as fc from 'fast-check'
import { filterPdfs } from './UploadPage.jsx'

// Arbitrary that generates mock file objects with various MIME types
const mimeTypes = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'text/plain',
  'application/msword',
  'application/zip',
]

const fileArbitrary = () =>
  fc.record({
    type: fc.oneof(...mimeTypes.map(m => fc.constant(m))),
    name: fc.string({ minLength: 1, maxLength: 20 }),
  })

describe('filterPdfs — Property 7', () => {
  it('only PDFs reach the file list for any mixed array of files', () => {
    // **Validates: Requirements 1.4**
    fc.assert(
      fc.property(fc.array(fileArbitrary()), files => {
        const result = filterPdfs(files)
        return result.every(f => f.type === 'application/pdf')
      })
    )
  })
})
