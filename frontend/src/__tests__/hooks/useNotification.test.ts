/**
 * Testes para hook useNotification
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useNotification } from '@/hooks/useNotification'

describe('useNotification', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('initializes with null notification', () => {
    const { result } = renderHook(() => useNotification())
    expect(result.current.notification).toBeNull()
  })

  it('shows notification with showNotification', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.showNotification('Test message')
    })

    expect(result.current.notification).not.toBeNull()
    expect(result.current.notification?.message).toBe('Test message')
    expect(result.current.notification?.type).toBe('info')
  })

  it('shows notification with custom type', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.showNotification('Error message', 'error')
    })

    expect(result.current.notification?.type).toBe('error')
  })

  it('hides notification manually', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.showNotification('Test message')
    })

    expect(result.current.notification).not.toBeNull()

    act(() => {
      result.current.hideNotification()
    })

    expect(result.current.notification).toBeNull()
  })

  it('auto-hides notification after duration', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.showNotification('Test message', 'info', 1000)
    })

    expect(result.current.notification).not.toBeNull()

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.notification).toBeNull()
  })

  it('uses default duration of 4000ms', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.showNotification('Test message')
    })

    expect(result.current.notification).not.toBeNull()

    act(() => {
      vi.advanceTimersByTime(3999)
    })
    expect(result.current.notification).not.toBeNull()

    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(result.current.notification).toBeNull()
  })

  it('success() shows success notification', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.success('Success!')
    })

    expect(result.current.notification?.type).toBe('success')
    expect(result.current.notification?.message).toBe('Success!')
  })

  it('error() shows error notification', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.error('Error!')
    })

    expect(result.current.notification?.type).toBe('error')
  })

  it('warning() shows warning notification', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.warning('Warning!')
    })

    expect(result.current.notification?.type).toBe('warning')
  })

  it('info() shows info notification', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.info('Info!')
    })

    expect(result.current.notification?.type).toBe('info')
  })

  it('replaces existing notification when new one is shown', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.showNotification('First message')
    })

    // Avancar tempo para garantir ID diferente
    act(() => {
      vi.advanceTimersByTime(1)
    })

    act(() => {
      result.current.showNotification('Second message')
    })

    expect(result.current.notification?.message).toBe('Second message')
  })

  it('clears previous timeout when showing new notification', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.showNotification('First', 'info', 5000)
    })

    act(() => {
      vi.advanceTimersByTime(2000)
    })

    act(() => {
      result.current.showNotification('Second', 'info', 5000)
    })

    act(() => {
      vi.advanceTimersByTime(3000)
    })

    // Second notification should still be visible (only 3s passed)
    expect(result.current.notification?.message).toBe('Second')
  })

  it('generates id based on timestamp', () => {
    const { result } = renderHook(() => useNotification())

    act(() => {
      result.current.showNotification('Test message')
    })

    // ID deve comecar com "notification-"
    expect(result.current.notification?.id).toMatch(/^notification-\d+$/)
  })
})
