import toast from 'react-hot-toast';

interface FetchOptions extends RequestInit {
  showToastOnError?: boolean;
}

export const apiFetch = async (url: string, options: FetchOptions = {}) => {
  const { showToastOnError = true, ...fetchOptions } = options;

  try {
    const response = await fetch(url, fetchOptions);

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch {
        // Not JSON
        const textData = await response.text();
        if (textData) errorMessage = textData.substring(0, 100);
      }

      if (showToastOnError) {
        toast.error(`API Error: ${errorMessage}`);
      }
      throw new Error(errorMessage);
    }

    return response;
  } catch (error) {
    if (showToastOnError && error instanceof Error && !error.message.startsWith('API Error')) {
      toast.error(`Network Error: ${error instanceof Error ? error.message : String(error)}`);
    }
    throw error;
  }
};
