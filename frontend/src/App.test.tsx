import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import LandingPage from './components/landing/LandingPage';
import {api} from './api';

jest.mock('react-router-dom',()=>({
  Link:({to,children}:{to:string;children:React.ReactNode})=>{
    const react=require('react');
    return react.createElement('a',{href:to},children);
  },
}));
jest.mock('./api',()=>({
  api:{get:jest.fn()},
  getStoredUser:()=>null,
  clearAuth:jest.fn(),
}));

test('landing page loads heritage sites and links to the planner', async () => {
  (api.get as jest.Mock).mockResolvedValue({data:{items:[{
    id:101,name:'Manek Chowk',lat:23.023611,lng:72.588611,
    categories:['markets_food'],visit_minutes:30,confidence:'low',hours_verified:false
  }]}});
  render(<LandingPage />);
  expect(screen.getByRole('link',{name:/plan my heritage walk/i})).toHaveAttribute('href','/planning');
  await waitFor(()=>expect(screen.getByText('Manek Chowk')).toBeInTheDocument());
  expect(screen.getByText(/confirm opening hours locally/i)).toBeInTheDocument();
});
