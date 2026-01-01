import axios from 'axios';

const API_URL = import.meta.env.PROD ? '' : 'http://127.0.0.1:8000';

export const registerFace = async (name, age, height, weight, imageFile) => {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('age', age);
    formData.append('height', height);
    formData.append('weight', weight);
    formData.append('file', imageFile);
    return axios.post(`${API_URL}/register`, formData);
};

export const recognizeFace = async (imageFile) => {
    const formData = new FormData();
    formData.append('file', imageFile);
    return axios.post(`${API_URL}/recognize`, formData);
};

export const chatWithAI = async (message, name, age, height, weight, faceId) => {
    return axios.post(`${API_URL}/chat`, {
        message,
        name,
        age,
        height,
        weight,
        face_id: faceId
    });
};

export const getChatHistory = async (faceId) => {
    return axios.get(`${API_URL}/chat/history/${faceId}`);
};
