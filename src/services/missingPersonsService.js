import { API } from '../config/api';

export const missingPersonsService = {
  // Get all missing persons
  async getAll() {
    try {
      const response = await fetch(API.missingPersons);
      if (!response.ok) {
        throw new Error('Failed to fetch missing persons');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching missing persons:', error);
      throw error;
    }
  },

  // Get a specific missing person by ID
  async getById(id) {
    try {
      const response = await fetch(API.missingPerson(id));
      if (!response.ok) {
        throw new Error('Failed to fetch missing person');
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching missing person:', error);
      throw error;
    }
  },

  // Create a new missing person
  async create(missingPersonData) {
    try {
      const response = await fetch(API.missingPersons, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(missingPersonData),
      });
      if (!response.ok) {
        throw new Error('Failed to create missing person');
      }
      return await response.json();
    } catch (error) {
      console.error('Error creating missing person:', error);
      throw error;
    }
  },

  // Update a missing person
  async update(id, updateData) {
    try {
      const response = await fetch(API.missingPerson(id), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });
      if (!response.ok) {
        throw new Error('Failed to update missing person');
      }
      return await response.json();
    } catch (error) {
      console.error('Error updating missing person:', error);
      throw error;
    }
  },

  // Delete a missing person
  async delete(id) {
    try {
      const response = await fetch(API.missingPerson(id), {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete missing person');
      }
      return true;
    } catch (error) {
      console.error('Error deleting missing person:', error);
      throw error;
    }
  },

  // Upload image and get URL
  async uploadImage(file) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(API.targetUpload, {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error('Failed to upload image');
      }
      
      const result = await response.json();
      return result.url || result.path; // Adjust based on your API response
    } catch (error) {
      console.error('Error uploading image:', error);
      throw error;
    }
  }
};
