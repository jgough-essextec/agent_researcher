import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { api } from '@/lib/api';

describe('API Client', () => {
  const mockFetch = vi.fn();

  beforeEach(() => {
    global.fetch = mockFetch;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('createResearch', () => {
    it('sends POST request with correct data', async () => {
      const mockResponse = {
        id: '123',
        client_name: 'Test Corp',
        status: 'pending',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.createResearch({
        client_name: 'Test Corp',
        sales_history: 'Previous sales',
        prompt: 'Research prompt',
      });

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/research/',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            client_name: 'Test Corp',
            sales_history: 'Previous sales',
            prompt: 'Research prompt',
          }),
        })
      );

      expect(result).toEqual(mockResponse);
    });

    it('throws error on failed request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'Bad request' }),
      });

      await expect(
        api.createResearch({
          client_name: '',
          sales_history: '',
          prompt: '',
        })
      ).rejects.toThrow('Bad request');
    });
  });

  describe('getResearch', () => {
    it('sends GET request with correct ID', async () => {
      const mockResponse = {
        id: '123',
        client_name: 'Test Corp',
        status: 'completed',
        result: 'Research results',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.getResearch('123');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/research/123/',
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('getDefaultPrompt', () => {
    it('fetches default prompt', async () => {
      const mockResponse = {
        id: 1,
        name: 'default',
        content: 'Prompt content',
        is_default: true,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.getDefaultPrompt();

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/prompts/default/',
        expect.objectContaining({
          headers: {
            'Content-Type': 'application/json',
          },
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });

  describe('updateDefaultPrompt', () => {
    it('sends PUT request with content', async () => {
      const mockResponse = {
        id: 1,
        name: 'default',
        content: 'Updated content',
        is_default: true,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.updateDefaultPrompt('Updated content');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/prompts/default/',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify({ content: 'Updated content' }),
        })
      );

      expect(result).toEqual(mockResponse);
    });
  });
});
