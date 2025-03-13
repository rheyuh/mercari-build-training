const SERVER_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:9000';

export interface Item {
  id: number;
  name: string;
  category: string;
  image_name: string;
}

export interface ItemListResponse {
  items: Item[];
}

export const fetchItems = async (): Promise<ItemListResponse> => {
  const response = await fetch(`${SERVER_URL}/items`, {
    method: 'GET',
    mode: 'cors',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });
  const itemsWithImages = await Promise.all(
    response.json().map(async (item: Item) => {
      try {
        const imageResponse = await fetch(`http://your-api-url/image/${item.imageName}`);
        const blob = await imageResponse.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        // Return the item with its image URL
        return { ...item, imageUrl };
      } catch (error) {
        console.error(`Error fetching image for item ${item.id}:`, error);
        // Return the item without an image URL if there was an error
        return item;
      }
    })
  );
  return response.json();
};

export const fetchImage = async (input: GetImageRequest): Promise<string> => {
  const response = await fetch(`${SERVER_URL}/image/${input.image}`, {
    method: 'GET',
    mode: 'cors',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
  });
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  return url;
};

export interface GetImageRequest {
  image: string;
}

export interface GetImageResponse {
  image: string;
}

export interface CreateItemInput {
  name: string;
  category: string;
  image: string | File;
}

export const postItem = async (input: CreateItemInput): Promise<Response> => {
  const data = new FormData();
  data.append('name', input.name);
  data.append('category', input.category);
  data.append('image', input.image);
  const response = await fetch(`${SERVER_URL}/items`, {
    method: 'POST',
    mode: 'cors',
    body: data,
  });
  return response;
};
