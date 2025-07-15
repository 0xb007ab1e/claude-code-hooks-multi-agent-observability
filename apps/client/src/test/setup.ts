import { expect, vi } from 'vitest'
import { config } from '@vue/test-utils'

// Mock Canvas API
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  clearRect: vi.fn(),
  fillRect: vi.fn(),
  strokeRect: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  arc: vi.fn(),
  stroke: vi.fn(),
  fill: vi.fn(),
  fillText: vi.fn(),
  measureText: vi.fn(() => ({ width: 0 })),
  save: vi.fn(),
  restore: vi.fn(),
  scale: vi.fn(),
  translate: vi.fn(),
  rotate: vi.fn(),
  drawImage: vi.fn(),
  createLinearGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
  createRadialGradient: vi.fn(() => ({
    addColorStop: vi.fn(),
  })),
  setLineDash: vi.fn(),
  getLineDash: vi.fn(() => []),
  closePath: vi.fn(),
  clip: vi.fn(),
}))

// Mock WebSocket
class MockWebSocket {
  constructor(url: string) {
    this.url = url
  }
  url: string
  readyState = 1
  send = vi.fn()
  close = vi.fn()
  addEventListener = vi.fn()
  removeEventListener = vi.fn()
  onopen = vi.fn()
  onclose = vi.fn()
  onmessage = vi.fn()
  onerror = vi.fn()
}

// @ts-ignore
global.WebSocket = MockWebSocket

// Mock ResizeObserver
class MockResizeObserver {
  constructor(callback: Function) {
    this.callback = callback
  }
  callback: Function
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

// @ts-ignore
global.ResizeObserver = MockResizeObserver

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Configure Vue Test Utils
config.global.stubs = {
  // Stub out any components that might cause issues in tests
  teleport: true,
  transition: true,
  'transition-group': true,
}

// Add custom matchers if needed
// expect.extend({
//   // custom matchers
// })
