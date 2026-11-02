import React from 'react';

const HistorySection: React.FC = () => {
  // Heritage sites data - using static content for basic display
  const heritageSites = [
    {
      id: '1',
      name: 'Jama Masjid',
      period: 'Mughal Period',
      significance: 'The Friday Mosque of Ahmedabad, a stunning example of Indo-Islamic architecture built in 1423.',
    },
    {
      id: '2',
      name: 'Sidi Sayyid Mosque',
      period: 'Mughal Period',
      significance: 'Famous for its intricate stone lattice work (jalis), a masterpiece of Gujarat\'s craftsmen.',
    },
    {
      id: '3',
      name: 'Adalaj Stepwell',
      period: 'Sultanate Period',
      significance: 'A five-story stepwell combining Hindu, Islamic and Indian architectural styles, built in 1498.',
    },
    {
      id: '4',
      name: 'Sabarmati Ashram',
      period: 'Independence Era',
      significance: 'Mahatma Gandhi\'s headquarters during the Indian independence movement, located on the banks of the Sabarmati river.',
    },
    {
      id: '5',
      name: 'Kankaria Lake',
      period: 'Colonial Period',
      significance: 'Ahmedabad\'s largest recreational lake, built in 1451, offering boating and zoo facilities.',
    },
  ];

  return (
    <section className="mb-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        Heritage Sites
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {heritageSites.map((site) => (
          <div
            key={site.id}
            className="p-4 rounded-lg bg-white shadow-sm border border-gray-200 hover:border-indigo-500 transition-colors"
          >
            <h3 className="text-font-medium text-gray-700 mb-1">
              {site.name}
            </h3>
            <p className="text-xs text-indigo-500 mb-2">
              {site.period}
            </p>
            <p className="text-xs text-gray-500 line-clamp-2">
              {site.significance}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
};

export default HistorySection;