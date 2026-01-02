/**
 * Testes para hook useLocalStorage
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useLocalStorage } from '@/hooks/useLocalStorage'

describe('useLocalStorage', () => {
  const localStorageMock = window.localStorage as {
    getItem: ReturnType<typeof vi.fn>
    setItem: ReturnType<typeof vi.fn>
    removeItem: ReturnType<typeof vi.fn>
  }

  beforeEach(() => {
    localStorageMock.getItem.mockClear()
    localStorageMock.setItem.mockClear()
    localStorageMock.removeItem.mockClear()
  })

  it('returns initial value when localStorage is empty', () => {
    localStorageMock.getItem.mockReturnValue(null)

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'))

    expect(result.current[0]).toBe('default')
  })

  it('returns stored value from localStorage', () => {
    localStorageMock.getItem.mockReturnValue(JSON.stringify('stored-value'))

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'))

    expect(result.current[0]).toBe('stored-value')
  })

  it('saves value to localStorage', () => {
    localStorageMock.getItem.mockReturnValue(null)

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'))

    act(() => {
      result.current[1]('new-value')
    })

    expect(localStorageMock.setItem).toHaveBeenCalledWith('test-key', JSON.stringify('new-value'))
    expect(result.current[0]).toBe('new-value')
  })

  it('removes value from localStorage', () => {
    localStorageMock.getItem.mockReturnValue(JSON.stringify('stored-value'))

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'))

    act(() => {
      result.current[2]() // removeValue
    })

    expect(localStorageMock.removeItem).toHaveBeenCalledWith('test-key')
    expect(result.current[0]).toBe('default')
  })

  it('handles object values', () => {
    localStorageMock.getItem.mockReturnValue(null)

    const initialValue = { name: 'Test', count: 0 }
    const { result } = renderHook(() => useLocalStorage('test-key', initialValue))

    expect(result.current[0]).toEqual(initialValue)

    act(() => {
      result.current[1]({ name: 'Updated', count: 1 })
    })

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'test-key',
      JSON.stringify({ name: 'Updated', count: 1 })
    )
  })

  it('handles array values', () => {
    localStorageMock.getItem.mockReturnValue(null)

    const { result } = renderHook(() => useLocalStorage<string[]>('test-key', []))

    act(() => {
      result.current[1](['item1', 'item2'])
    })

    expect(result.current[0]).toEqual(['item1', 'item2'])
  })

  it('accepts function updater', () => {
    localStorageMock.getItem.mockReturnValue(JSON.stringify(10))

    const { result } = renderHook(() => useLocalStorage('test-key', 0))

    act(() => {
      result.current[1]((prev) => prev + 5)
    })

    expect(result.current[0]).toBe(15)
  })

  it('handles boolean values', () => {
    localStorageMock.getItem.mockReturnValue(null)

    const { result } = renderHook(() => useLocalStorage('test-key', false))

    expect(result.current[0]).toBe(false)

    act(() => {
      result.current[1](true)
    })

    expect(result.current[0]).toBe(true)
    expect(localStorageMock.setItem).toHaveBeenCalledWith('test-key', 'true')
  })

  it('handles JSON parse error gracefully', () => {
    localStorageMock.getItem.mockReturnValue('invalid-json')
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'))

    expect(result.current[0]).toBe('default')
    expect(consoleSpy).toHaveBeenCalled()

    consoleSpy.mockRestore()
  })

  it('handles setItem error gracefully', () => {
    localStorageMock.getItem.mockReturnValue(null)
    localStorageMock.setItem.mockImplementation(() => {
      throw new Error('QuotaExceeded')
    })
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'))

    act(() => {
      result.current[1]('new-value')
    })

    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('handles removeItem error gracefully', () => {
    localStorageMock.getItem.mockReturnValue(JSON.stringify('value'))
    localStorageMock.removeItem.mockImplementation(() => {
      throw new Error('Error')
    })
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    const { result } = renderHook(() => useLocalStorage('test-key', 'default'))

    act(() => {
      result.current[2]()
    })

    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })
})
