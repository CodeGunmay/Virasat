import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { api, AuthResponse, setAuth } from '../../api';

export default function RegisterPage() {
  const navigate=useNavigate();
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();setBusy(true);setError('');
    try {
      const {data}=await api.post<AuthResponse>('/auth/register',{email,password,role:'visitor'});
      setAuth(data);navigate('/planning');
    } catch(e) {
      setError(axios.isAxiosError(e) && e.response?.status===409?'That email is already registered.':'Registration failed. Check your details and try again.');
    } finally {setBusy(false);}
  }
  return <main className="max-w-md mx-auto mt-10 p-6 rounded-xl shadow bg-white">
    <h1 className="text-3xl font-bold text-indigo-900">Join Virasat</h1>
    <form onSubmit={submit} className="space-y-4 mt-4">
      <label className="block">Email<input className="block w-full border rounded p-2" type="email" required autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)}/></label>
      <label className="block">Password (8–72 characters)<input className="block w-full border rounded p-2" type="password" required minLength={8} maxLength={72} autoComplete="new-password" value={password} onChange={e=>setPassword(e.target.value)}/></label>
      {error && <p role="alert" className="text-red-700">{error}</p>}
      <button disabled={busy} className="bg-indigo-800 text-white rounded px-4 py-2">{busy?'Creating account…':'Register'}</button>
    </form>
    <p className="mt-4"><Link to="/login" className="text-indigo-700 underline">Already registered? Sign in</Link></p>
  </main>;
}
