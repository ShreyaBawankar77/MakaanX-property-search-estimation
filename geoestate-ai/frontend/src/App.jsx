import { useEffect, useMemo, useRef, useState } from 'react';
// react-leaflet map removed from neighborhood section per user request

const amenityOptions = ['Gymnasium', 'SwimmingPool', 'CarParking', '24X7Security', 'LiftAvailable', 'ClubHouse'];
const featureLabels = {
  area_sqft: 'Home size',
  bhk: 'Bedrooms',
  city: 'City',
  locality: 'Area',
  resale: 'Home type',
  Gymnasium: 'Gym',
  SwimmingPool: 'Swimming pool',
  CarParking: 'Parking',
  '24X7Security': '24/7 security',
  LiftAvailable: 'Lift',
  ClubHouse: 'Clubhouse',
};
const formatFeatureLabel = (feature) => featureLabels[feature] || feature.replace(/_/g, ' ');

const defaultForm = {
  city: 'Mumbai',
  locality: '',
  bhk: '',
  area_sqft: '',
  resale: '',
  listing_price: '',
  amenities: '',
};

const cityImageMap = {
  Mumbai: [
    'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80',
  ],
  Delhi: [
    'https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1460317442991-0ec209397118?auto=format&fit=crop&w=1200&q=80',
  ],
  Bengaluru: [
    'https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1554995207-c18c203602cb?auto=format&fit=crop&w=1200&q=80',
  ],
  Hyderabad: [
    'https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1448630360428-65456885c650?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1523217582562-09d0def993a6?auto=format&fit=crop&w=1200&q=80',
  ],
  Chennai: [
    'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80',
  ],
  Kolkata: [
    'https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1554995207-c18c203602cb?auto=format&fit=crop&w=1200&q=80',
  ],
  Pune: [
    'https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1460317442991-0ec209397118?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80',
  ],
  Ahmedabad: [
    'https://images.unsplash.com/photo-1484154218962-a197022b5858?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1523217582562-09d0def993a6?auto=format&fit=crop&w=1200&q=80',
  ],
  Jaipur: [
    'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1494526585095-c41746248156?auto=format&fit=crop&w=1200&q=80',
  ],
  Lucknow: [
    'https://images.unsplash.com/photo-1554995207-c18c203602cb?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1570129477492-45c003edd2be?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1448630360428-65456885c650?auto=format&fit=crop&w=1200&q=80',
  ],
  Kochi: [
    'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1568605114967-8130f3a36994?auto=format&fit=crop&w=1200&q=80',
    'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1200&q=80',
  ],
};

const getCityPropertyImage = (city, locality, fallbackIndex = 0) => {
  const currentCity = city || 'Mumbai';
  const cityImages = cityImageMap[currentCity] || cityImageMap.Mumbai;
  const seed = (locality ? locality.length : 0) + fallbackIndex;
  return cityImages[seed % cityImages.length];
};

const getPropertyCardImage = (property, fallbackIndex = 0) => {
  if (property?.image_url && !/placeholder|svg/i.test(property.image_url)) {
    return property.image_url;
  }
  return getCityPropertyImage(property?.city, property?.locality, fallbackIndex || property?.id || 1);
};

const getPropertyName = (property) => `${property?.bhk || 'Home'} BHK home`;

const getGoogleMapsEmbedUrl = (query) => {
  const search = typeof query === 'string' ? `${query}, India` : `${query.latitude},${query.longitude}`;
  const zoom = typeof query === 'string' ? 13 : 16;
  return `https://www.google.com/maps?output=embed&q=${encodeURIComponent(search)}&z=${zoom}`;
};

const getGoogleMapsUrl = (query) => {
  const search = typeof query === 'string' ? `${query}, India` : `${query.latitude},${query.longitude}`;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(search)}`;
};

const getLifestyleHighlights = (property) => {
  const amenities = (property?.amenities || '').toLowerCase();
  const highlights = [];
  if (/gymnasium|swimmingpool|joggingtrack|sportsfacility/.test(amenities)) highlights.push('Active living');
  if (/24x7security|intercom|cctv/.test(amenities)) highlights.push('Added security');
  if (/clubhouse|indoorgames|children'splayarea/.test(amenities)) highlights.push('Community spaces');
  if (/carparking|liftavailable|powerbackup/.test(amenities)) highlights.push('Everyday convenience');
  return highlights;
};

const nearbySearches = [
  ['Schools', 'schools'],
  ['Hospitals', 'hospitals'],
  ['Transit', 'public transport'],
  ['Groceries', 'grocery stores'],
];

const defaultPrediction = null;
const listingPageSize = 24;

function formatAmenityDistance(distanceKm) {
  const dist = Number(distanceKm);
  if (!Number.isFinite(dist) || dist < 0) {
    return { label: 'Distance estimate unavailable', time: '', isWalk: false, badgeClass: 'dist-badge--neutral' };
  }
  if (dist === 0) {
    return { label: 'On-site · 0 m', time: 'Inside complex', isWalk: true, badgeClass: 'dist-badge--onsite' };
  }
  if (dist < 1) {
    const meters = Math.round(dist * 1000);
    const mins = Math.max(1, Math.round(meters / 80));
    return {
      label: `${meters} m away`,
      time: `~${mins} min walk`,
      isWalk: true,
      badgeClass: 'dist-badge--walk',
    };
  }
  const kmStr = dist.toFixed(dist < 10 ? 1 : 0);
  const driveMins = Math.max(2, Math.round(dist * 3));
  return {
    label: `${kmStr} km away`,
    time: `~${driveMins} min drive`,
    isWalk: false,
    badgeClass: 'dist-badge--drive',
  };
}

const categoryMeta = {
  Education: { icon: '🎓', label: 'Schools & Colleges', short: 'Education' },
  Healthcare: { icon: '🏥', label: 'Hospitals & Healthcare', short: 'Healthcare' },
  Transit: { icon: '🚇', label: 'Transit & Metro Stations', short: 'Transit' },
  'Groceries & daily needs': { icon: '🛒', label: 'Groceries & Daily Markets', short: 'Groceries' },
};

function AmenityDistanceExplorer({ property, report }) {
  const [activeCategory, setActiveCategory] = useState('all');

  const nearby = report?.nearby || {};
  const categories = Object.keys(nearby);

  const nearestByCategory = useMemo(() => {
    const summary = {};
    for (const [cat, places] of Object.entries(nearby)) {
      if (places && places.length > 0) {
        const sorted = [...places].sort((a, b) => (Number(a.distance_km) || 99) - (Number(b.distance_km) || 99));
        summary[cat] = sorted[0];
      }
    }
    return summary;
  }, [nearby]);

  const onsiteAmenities = useMemo(() => {
    return (property?.amenities || '')
      .split(',')
      .map((a) => a.trim())
      .filter(Boolean);
  }, [property?.amenities]);

  const displayedPlaces = useMemo(() => {
    if (activeCategory === 'onsite') return [];
    if (activeCategory === 'all') {
      const all = [];
      for (const [category, places] of Object.entries(nearby)) {
        for (const place of places) {
          all.push({ ...place, category });
        }
      }
      return all.sort((a, b) => (Number(a.distance_km) || 99) - (Number(b.distance_km) || 99));
    }
    return (nearby[activeCategory] || []).map((place) => ({ ...place, category: activeCategory }));
  }, [nearby, activeCategory]);

  return (
    <div className="amenity-distance-explorer">
      <div className="amenity-explorer-header">
        <div>
          <span className="amenity-explorer-kicker">NEIGHBOURHOOD AMENITY DISTANCES</span>
          <h4>📍 Proximity from {property.locality}, {property.city}</h4>
          <span className="amenity-explorer-subtitle">
            Measured walking & driving distances to key daily conveniences within {report?.radius_km || 2.5} km
          </span>
        </div>
      </div>

      <div className="amenity-quick-metrics">
        {Object.entries(nearestByCategory).map(([cat, place]) => {
          const meta = categoryMeta[cat] || { icon: '📍', label: cat, short: cat };
          const distInfo = formatAmenityDistance(place.distance_km);
          return (
            <div className="amenity-metric-card" key={cat}>
              <span className="amenity-metric-icon">{meta.icon}</span>
              <div className="amenity-metric-text">
                <span className="amenity-metric-category">{meta.short}</span>
                <strong className="amenity-metric-distance">{distInfo.label}</strong>
                <small className="amenity-metric-time">{distInfo.time}</small>
              </div>
            </div>
          );
        })}
        {onsiteAmenities.length > 0 && (
          <div className="amenity-metric-card amenity-metric-card--onsite">
            <span className="amenity-metric-icon">⭐</span>
            <div className="amenity-metric-text">
              <span className="amenity-metric-category">Society Amenities</span>
              <strong className="amenity-metric-distance">On-Site · 0 m</strong>
              <small className="amenity-metric-time">{onsiteAmenities.length} within complex</small>
            </div>
          </div>
        )}
      </div>

      <div className="amenity-category-tabs">
        <button
          type="button"
          className={`amenity-tab ${activeCategory === 'all' ? 'active' : ''}`}
          onClick={() => setActiveCategory('all')}
        >
          All Nearby ({displayedPlaces.length})
        </button>
        {categories.map((cat) => {
          const meta = categoryMeta[cat] || { icon: '📍', short: cat };
          const count = (nearby[cat] || []).length;
          return (
            <button
              type="button"
              key={cat}
              className={`amenity-tab ${activeCategory === cat ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat)}
            >
              {meta.icon} {meta.short} ({count})
            </button>
          );
        })}
        {onsiteAmenities.length > 0 && (
          <button
            type="button"
            className={`amenity-tab ${activeCategory === 'onsite' ? 'active' : ''}`}
            onClick={() => setActiveCategory('onsite')}
          >
            ⭐ On-Site ({onsiteAmenities.length})
          </button>
        )}
      </div>

      {activeCategory !== 'onsite' && (
        <div className="amenity-distance-list">
          {displayedPlaces.length > 0 ? (
            displayedPlaces.map((place, idx) => {
              const meta = categoryMeta[place.category] || { icon: '📍', short: place.category, label: place.category };
              const distInfo = formatAmenityDistance(place.distance_km);
              return (
                <div className="amenity-distance-card" key={`${place.name}-${idx}`}>
                  <div className="amenity-card-icon">{meta.icon}</div>
                  <div className="amenity-card-main">
                    <div className="amenity-card-name-row">
                      <span className="amenity-card-name">{place.name}</span>
                      <span className="amenity-kind-pill">{place.kind || meta.short}</span>
                    </div>
                    <span className="amenity-card-category">{meta.label}</span>
                  </div>
                  <div className="amenity-card-distance-col">
                    <span className={`amenity-dist-badge ${distInfo.badgeClass}`}>
                      {distInfo.isWalk ? '🚶' : '🚗'} {distInfo.label}
                    </span>
                    <small className="amenity-time-estimate">{distInfo.time}</small>
                  </div>
                </div>
              );
            })
          ) : (
            <p className="empty-amenities">No nearby amenities found for this category.</p>
          )}
        </div>
      )}

      {(activeCategory === 'all' || activeCategory === 'onsite') && onsiteAmenities.length > 0 && (
        <div className="amenity-onsite-box">
          <div className="amenity-onsite-header">
            <div>
              <strong>⭐ On-Site Society Complex Amenities</strong>
              <span>Available inside the residential premises (0 m distance)</span>
            </div>
            <span className="amenity-dist-badge dist-badge--onsite">0 m · Inside Complex</span>
          </div>
          <div className="amenity-onsite-pills">
            {onsiteAmenities.map((amenity) => (
              <span className="amenity-onsite-pill" key={amenity}>
                ✓ {formatFeatureLabel(amenity)}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="amenity-footnote">
        <small>
          {report?.distance_note || 'Straight-line distances measured from this locality.'}
        </small>
      </div>
    </div>
  );
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDistance(distanceKm) {
  const distance = Number(distanceKm);
  if (!Number.isFinite(distance) || distance < 0) return 'Distance unavailable';
  if (distance < 1) return `${Math.round(distance * 1000)} m away`;
  return `${distance.toFixed(distance < 10 ? 1 : 0)} km away`;
}

function describeFilters(filters) {
  return [
    filters.locality || (filters.city ? `Any area in ${filters.city}` : 'Any area'),
    filters.bhk ? `${filters.bhk} BHK` : 'Any BHK',
    Number(filters.min_price) > 0 ? `from ${formatCurrency(filters.min_price)}` : null,
    filters.max_price != null && filters.max_price !== '' ? `up to ${formatCurrency(filters.max_price)}` : 'Any budget',
    filters.area_sqft ? `around ${Number(filters.area_sqft).toLocaleString()} sq. ft.` : null,
    filters.resale == null ? 'Any home type' : Number(filters.resale) ? 'Resale' : 'New home',
    filters.amenities ? filters.amenities.split(',').map(formatFeatureLabel).join(', ') : 'Any features',
  ].filter(Boolean).join(' · ');
}

function formatBudgetFriendly(val) {
  const n = Number(val);
  if (!n || n <= 0) return 'No limit';
  if (n >= 10000000) {
    const cr = n / 10000000;
    return `₹${cr % 1 === 0 ? cr : cr.toFixed(2)} Cr`;
  }
  if (n >= 100000) {
    const l = n / 100000;
    return `₹${l % 1 === 0 ? l : l.toFixed(1)} Lakh`;
  }
  return `₹${n.toLocaleString('en-IN')}`;
}

async function fetchWithRetry(url, options = {}, retries = 2, delay = 500) {
  try {
    const res = await fetch(url, options);
    if (!res.ok && retries > 0 && res.status >= 500) {
      await new Promise((resolve) => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, delay * 1.5);
    }
    return res;
  } catch (err) {
    if (retries > 0 && err.name !== 'AbortError') {
      await new Promise((resolve) => setTimeout(resolve, delay));
      return fetchWithRetry(url, options, retries - 1, delay * 1.5);
    }
    throw err;
  }
}

function App() {
  const [form, setForm] = useState(defaultForm);
  const [budget, setBudget] = useState('30000000');
  const [minimumPrice, setMinimumPrice] = useState('');
  const [appliedBudget, setAppliedBudget] = useState('30000000');
  const [appliedMinimumPrice, setAppliedMinimumPrice] = useState('');
  const [searchPriceError, setSearchPriceError] = useState('');
  const [appliedCity, setAppliedCity] = useState(defaultForm.city);
  const [appliedLocality, setAppliedLocality] = useState(defaultForm.locality);
  const [signedInUser, setSignedInUser] = useState(null);
  const [authMessage, setAuthMessage] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState('signin');
  const [authForm, setAuthForm] = useState({ name: '', email: '', password: '' });
  const [predictionHistory, setPredictionHistory] = useState([]);
  const [googleClientId, setGoogleClientId] = useState(import.meta.env.VITE_GOOGLE_CLIENT_ID || '');
  const [historyOpen, setHistoryOpen] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const [cityOptions, setCityOptions] = useState([]);
  const [availableLocalities, setAvailableLocalities] = useState([]);
  const [result, setResult] = useState(defaultPrediction);
  const [predicting, setPredicting] = useState(false);
  const [predictError, setPredictError] = useState('');
  const [properties, setProperties] = useState([]);
  const [totalProperties, setTotalProperties] = useState(0);
  const [listingPage, setListingPage] = useState(0);
  const [hasSearched, setHasSearched] = useState(false);
  const [selectedPropertyId, setSelectedPropertyId] = useState('');
  const [appliedFilters, setAppliedFilters] = useState({ bhk: null, resale: null, area_sqft: null, area_tolerance: 0.2, amenities: '' });
  const [fallbackProperties, setFallbackProperties] = useState([]);
  const [fallbackMode, setFallbackMode] = useState('city_budget');
  const [budgetCoach, setBudgetCoach] = useState(null);
  const [neighborhoodReport, setNeighborhoodReport] = useState(null);
  const [neighborhoodReportKey, setNeighborhoodReportKey] = useState('');
  const [neighborhoodLoadingKey, setNeighborhoodLoadingKey] = useState('');
  const [neighborhoodError, setNeighborhoodError] = useState('');
  const [neighborhoodMapCategory, setNeighborhoodMapCategory] = useState('Schools');
  const [mapPanel, setMapPanel] = useState(null);
  const [assistantOpen, setAssistantOpen] = useState(false);
  const [assistantDraft, setAssistantDraft] = useState('');
  const [assistantBusy, setAssistantBusy] = useState(false);
  const [assistantMessages, setAssistantMessages] = useState([
    { role: 'assistant', text: 'Tell me where you want to live, your budget, number of bedrooms, or home features. I will find matching homes.' },
  ]);

  const propertySuggestions = properties;
  const neighborhoodAbortRef = useRef(null);
  const mapRequestIdRef = useRef(0);

  const openMapPanel = (query, title = 'Google Maps') => {
    setMapPanel({ query, title, googleMapsUrl: getGoogleMapsUrl(query) });
  };

  const openAreaMap = async (property) => {
    const requestId = mapRequestIdRef.current + 1;
    mapRequestIdRef.current = requestId;
    const title = `${property.locality}, ${property.city}`;
    setMapPanel({ title, loading: true, error: '' });
    try {
      const params = new URLSearchParams({ city: property.city, locality: property.locality });
      const response = await fetch(`/api/location/geocode?${params.toString()}`);
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'This area could not be located.');
      if (mapRequestIdRef.current === requestId) {
        setMapPanel({
          title,
          displayName: data.display_name || title,
          query: { latitude: data.latitude, longitude: data.longitude },
          googleMapsUrl: getGoogleMapsUrl({ latitude: data.latitude, longitude: data.longitude }),
          loading: false,
          notice: 'Showing the locality area. The source listing does not include exact property coordinates.',
        });
      }
    } catch {
      if (mapRequestIdRef.current === requestId) {
        const searchQuery = `${property.locality}, ${property.city}`;
        setMapPanel({
          title,
          query: searchQuery,
          googleMapsUrl: getGoogleMapsUrl(searchQuery),
          loading: false,
          notice: `Exact locality coordinates could not be resolved. Showing Google Maps results for this area, not the city centre. Property-level coordinates are not in the source dataset.`,
        });
      }
    }
  };

  const closeMapPanel = () => {
    mapRequestIdRef.current += 1;
    setMapPanel(null);
  };

  useEffect(() => {
    if (!mapPanel) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') closeMapPanel();
    };
    window.addEventListener('keydown', closeOnEscape);
    return () => window.removeEventListener('keydown', closeOnEscape);
  }, [mapPanel]);

  const activePrediction = result || {
    predicted_price: 0,
    estimated_range: { lower: 0, upper: 0 },
    price_per_sqft: 0,
    confidence: 0,
    fairness: 'No estimate yet',
    explanation: { top_factors: [] },
  };
  const workflowStep = selectedPropertyId ? 3 : hasSearched ? 2 : 1;

  useEffect(() => {
    fetch('/api/auth/session')
      .then((response) => response.json())
      .then((data) => setSignedInUser(data.user || null))
      .catch(() => {});
  }, []);

  useEffect(() => {
    let active = true;
    fetch('/api/config')
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Google sign-in configuration could not be loaded.');
        if (active && data.google_client_id) setGoogleClientId(data.google_client_id);
      })
      .catch((error) => console.error('Google sign-in configuration could not be loaded.', error));
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!googleClientId) return undefined;

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => {
      window.google?.accounts.id.initialize({
        client_id: googleClientId,
        callback: async ({ credential }) => {
          setAuthLoading(true);
          setAuthMessage('');
          try {
            const response = await fetch('/api/auth/google', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ credential }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Google sign-in failed.');
            setSignedInUser(data.user);
            setAuthOpen(false);
          } catch (error) {
            setAuthMessage(error.message || 'Google sign-in failed.');
          } finally {
            setAuthLoading(false);
          }
        },
      });
      const buttonRoot = document.getElementById('google-signin-button');
      if (buttonRoot) {
        window.google.accounts.id.renderButton(buttonRoot, {
          theme: 'outline',
          size: 'large',
          shape: 'pill',
          text: 'continue_with',
        });
      }
    };
    script.onerror = () => setAuthMessage('Google sign-in could not be loaded.');
    document.head.appendChild(script);
    return () => script.remove();
  }, [googleClientId]);

  useEffect(() => {
    if (!signedInUser) {
      setPredictionHistory([]);
      setHistoryError('');
      setHistoryLoading(false);
      return undefined;
    }

    const controller = new AbortController();
    setHistoryLoading(true);
    setHistoryError('');
    fetch('/api/auth/history', { signal: controller.signal })
      .then(async (response) => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Saved estimates could not be loaded.');
        setPredictionHistory(data.history || []);
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setHistoryError(error.message || 'Saved estimates could not be loaded.');
      })
      .finally(() => {
        if (!controller.signal.aborted) setHistoryLoading(false);
      });

    return () => controller.abort();
  }, [signedInUser]);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams();
    if (form.city) params.set('city', form.city);
    fetchWithRetry(`/api/properties/options?${params.toString()}`, { signal: controller.signal })
      .then((response) => response.json())
      .then((data) => {
        setCityOptions(data.cities || []);
        setAvailableLocalities(data.localities || []);
        setForm((previous) => {
          const city = data.cities?.includes(previous.city) ? previous.city : data.cities?.[0] || '';
          const locality = data.localities?.includes(previous.locality) ? previous.locality : '';
          return city === previous.city && locality === previous.locality ? previous : { ...previous, city, locality };
        });
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setCityOptions([]);
          setAvailableLocalities([]);
        }
      });
    return () => controller.abort();
  }, [form.city]);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams();
    if (appliedCity) params.set('city', appliedCity);
    if (appliedLocality) params.set('locality', appliedLocality);
    if (appliedBudget !== '') params.set('max_price', appliedBudget);
    if (appliedMinimumPrice !== '') params.set('min_price', appliedMinimumPrice);
    if (appliedFilters.bhk) params.set('bhk', appliedFilters.bhk);
    if (appliedFilters.resale !== null) params.set('resale', appliedFilters.resale);
    if (appliedFilters.area_sqft) params.set('area_sqft', appliedFilters.area_sqft);
    params.set('area_tolerance', appliedFilters.area_tolerance ?? 0.2);
    if (appliedFilters.amenities) params.set('amenities', appliedFilters.amenities);
    params.set('limit', String(listingPageSize));
    params.set('offset', String(listingPage * listingPageSize));

    fetchWithRetry(`/api/properties?${params.toString()}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error('Property listings could not be loaded.');
        const data = await response.json();
        if (!Array.isArray(data)) {
          setProperties([]);
          setTotalProperties(0);
          return;
        }
        setProperties(data);
        setTotalProperties(Number(response.headers.get('X-Total-Count')) || data.length);
      })
      .catch((error) => {
        if (error.name !== 'AbortError') {
          setProperties([]);
          setTotalProperties(0);
        }
      });
    return () => controller.abort();

  }, [appliedCity, appliedLocality, appliedBudget, appliedMinimumPrice, appliedFilters, listingPage]);

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams();
    if (appliedCity) params.set('city', appliedCity);
    if (appliedLocality) params.set('locality', appliedLocality);
    if (appliedBudget !== '') params.set('max_price', appliedBudget);
    if (appliedMinimumPrice !== '') params.set('min_price', appliedMinimumPrice);
    if (appliedFilters.bhk) params.set('bhk', appliedFilters.bhk);
    if (appliedFilters.resale !== null) params.set('resale', appliedFilters.resale);
    if (appliedFilters.area_sqft) params.set('area_sqft', appliedFilters.area_sqft);
    params.set('area_tolerance', appliedFilters.area_tolerance ?? 0.2);
    if (appliedFilters.amenities) params.set('amenities', appliedFilters.amenities);
    fetch(`/api/budget/coach?${params.toString()}`, { signal: controller.signal })
      .then((response) => response.json())
      .then((data) => setBudgetCoach(data))
      .catch((error) => {
        if (error.name !== 'AbortError') setBudgetCoach(null);
      });
    return () => controller.abort();
  }, [appliedCity, appliedLocality, appliedBudget, appliedMinimumPrice, appliedFilters]);

  useEffect(() => {
    if (properties.length > 0) {
      setFallbackProperties([]);
      return;
    }
    if (appliedMinimumPrice !== '') {
      setFallbackProperties([]);
      return undefined;
    }
    if (!appliedCity) return;
    const controller = new AbortController();

    const loadFallbacks = async () => {
      try {
        if (appliedLocality) {
          const locRes = await fetchWithRetry(`/api/properties?city=${encodeURIComponent(appliedCity)}&locality=${encodeURIComponent(appliedLocality)}&limit=12`, { signal: controller.signal });
          if (locRes.ok) {
            const locData = await locRes.json();
            if (Array.isArray(locData) && locData.length > 0) {
              setFallbackProperties(locData);
              setFallbackMode('locality_all');
              return;
            }
          }
        }
        const budgetParam = appliedBudget !== '' ? `&max_price=${encodeURIComponent(appliedBudget)}` : '';
        const cityRes = await fetchWithRetry(`/api/properties?city=${encodeURIComponent(appliedCity)}${budgetParam}&limit=12`, { signal: controller.signal });
        if (cityRes.ok) {
          const cityData = await cityRes.json();
          if (Array.isArray(cityData) && cityData.length > 0) {
            setFallbackProperties(cityData);
            setFallbackMode('city_budget');
            return;
          }
        }
        const allRes = await fetchWithRetry(`/api/properties?city=${encodeURIComponent(appliedCity)}&limit=12`, { signal: controller.signal });
        if (allRes.ok) {
          const allData = await allRes.json();
          if (Array.isArray(allData)) {
            setFallbackProperties(allData);
            setFallbackMode('city_all');
          }
        }
      } catch (err) {
        if (err.name !== 'AbortError') {
          setFallbackProperties([]);
        }
      }
    };

    loadFallbacks();
    return () => controller.abort();
  }, [properties.length, appliedCity, appliedLocality, appliedBudget, appliedMinimumPrice, appliedFilters]);

  const handleChange = (event) => {
    const { name, value } = event.target;

    if (name === 'city') {
      setForm((previous) => ({ ...previous, city: value, locality: '' }));
      setListingPage(0);
      setSelectedPropertyId('');
      setResult(null);
      return;
    }

    setForm((previous) => ({ ...previous, [name]: value }));
    if (name === 'locality') setListingPage(0);
    if (['locality', 'bhk', 'area_sqft', 'resale'].includes(name)) {
      setSelectedPropertyId('');
    }
    if (['locality', 'bhk', 'area_sqft', 'resale', 'listing_price'].includes(name)) {
      setResult(null);
      setPredictError('');
    }
  };

  const handlePredict = async (customPayload = null) => {
    const source = customPayload || form;
    if (!source.locality) {
      setPredictError('Please choose an area (locality) above to calculate an accurate price estimate.');
      return;
    }
    const body = {
      city: source.city,
      locality: source.locality,
      property_id: source.property_id || selectedPropertyId || null,
      bhk: Number(source.bhk) || 2,
      area_sqft: Number(source.area_sqft) || 1000,
      resale: source.resale === '' || source.resale == null ? 0 : Number(source.resale),
      listing_price: source.listing_price ? Number(source.listing_price) : null,
      amenities: source.amenities || '',
    };
    setPredicting(true);
    setPredictError('');
    try {
    const response = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not calculate price estimate.');
      setResult(data);
    if (signedInUser) {
      try {
        const historyResponse = await fetch('/api/auth/history', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ request: body, result: data }),
        });
        const historyData = await historyResponse.json();
        if (!historyResponse.ok) throw new Error(historyData.detail || 'Estimate could not be saved.');
        setPredictionHistory((previous) => [historyData.entry, ...previous].slice(0, 50));
      } catch (error) {
        setPredictError(`Estimate calculated, but it could not be saved: ${error.message || 'Please try again.'}`);
      }
    }
    } catch (err) {
    setPredictError(err.message || 'Price estimation failed.');
    } finally {
      setPredicting(false);
    }
  };

  const handleDemoSignIn = async () => {
    setAuthLoading(true);
    setAuthMessage('');
    try {
      const response = await fetch('/api/auth/demo', { method: 'POST' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Demo sign-in failed.');
      setSignedInUser(data.user);
      setAuthOpen(false);
    } catch (error) {
      setAuthMessage(error.message || 'Demo sign-in failed.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleAuthSubmit = async (event) => {
    event.preventDefault();
    setAuthLoading(true);
    setAuthMessage('');
    try {
      const registering = authMode === 'register';
      const response = await fetch(`/api/auth/${registering ? 'register' : 'login'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registering
          ? authForm
          : { email: authForm.email, password: authForm.password }),
      });
      const data = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(data.detail)
          ? data.detail.map((issue) => issue.msg).join(' ')
          : data.detail;
        throw new Error(detail || `Could not ${registering ? 'create account' : 'sign in'}.`);
      }
      setSignedInUser(data.user);
      setAuthForm({ name: '', email: '', password: '' });
      setAuthOpen(false);
    } catch (error) {
      setAuthMessage(error.message || 'Account access failed.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRestoreHistory = (entry) => {
    const savedRequest = entry.request || {};
    setForm((previous) => ({ ...previous, ...savedRequest }));
    setResult(entry.result || null);
    setHistoryOpen(false);
    document.getElementById('predict')?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSearch = () => {
    const minValue = minimumPrice.trim() === '' ? null : Number(minimumPrice);
    const maxValue = budget.trim() === '' ? null : Number(budget);
    if (minValue !== null && (!Number.isFinite(minValue) || minValue < 0)) {
      setSearchPriceError('Enter a valid minimum price of zero or more.');
      return;
    }
    if (maxValue !== null && (!Number.isFinite(maxValue) || maxValue < 0)) {
      setSearchPriceError('Enter a valid maximum price of zero or more.');
      return;
    }
    if (minValue !== null && maxValue !== null && minValue > maxValue) {
      setSearchPriceError('Minimum price cannot be greater than maximum price.');
      return;
    }
    setSearchPriceError('');
    setListingPage(0);
    setAppliedCity(form.city);
    setAppliedLocality(form.locality);
    setAppliedBudget(budget.trim());
    setAppliedMinimumPrice(minimumPrice.trim());
    setAppliedFilters({
      bhk: form.bhk ? Number(form.bhk) : null,
      resale: form.resale === '' || form.resale == null ? null : Number(form.resale),
      area_sqft: form.area_sqft ? Number(form.area_sqft) : null,
      area_tolerance: 0.2,
      amenities: form.amenities,
    });
    setHasSearched(true);
    setSelectedPropertyId('');
    setResult(null);
    document.getElementById('listings')?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSearchEstimateRange = () => {
    const lower = Math.max(0, Number(result?.estimated_range?.lower) || 0);
    const upper = Number(result?.estimated_range?.upper) || 0;
    if (upper <= 0 || lower > upper) return;

    const nextMinimum = lower > 0 ? String(Math.floor(lower)) : '';
    const nextMaximum = String(Math.ceil(upper));
    setMinimumPrice(nextMinimum);
    setBudget(nextMaximum);
    setAppliedMinimumPrice(nextMinimum);
    setAppliedBudget(nextMaximum);
    setSearchPriceError('');
    setAppliedCity(form.city);
    setAppliedLocality(form.locality);
    setAppliedFilters({
      bhk: form.bhk ? Number(form.bhk) : null,
      resale: form.resale === '' || form.resale == null ? null : Number(form.resale),
      area_sqft: form.area_sqft ? Number(form.area_sqft) : null,
      area_tolerance: 0.2,
      amenities: form.amenities,
    });
    setListingPage(0);
    setHasSearched(true);
    document.getElementById('listings')?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleUseListing = (property) => {
    setListingPage(0);
    setForm((previous) => ({
      ...previous,
      city: property.city,
      locality: property.locality,
      bhk: property.bhk,
      area_sqft: property.area_sqft,
      resale: property.resale,
      listing_price: property.listing_price,
      amenities: property.amenities || '',
    }));
    setSelectedPropertyId(property.property_id);
    setResult(null);
    setPredictError('');
    document.getElementById('predict')?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleNeighborhoodExplore = async (property, retry = false) => {
    const key = `${property.property_id}:${property.locality}:${property.city}`;
    if (neighborhoodReportKey === key && !retry) {
      neighborhoodAbortRef.current?.abort();
      setNeighborhoodReportKey('');
      setNeighborhoodLoadingKey('');
      setNeighborhoodError('');
      return;
    }
    neighborhoodAbortRef.current?.abort();
    const controller = new AbortController();
    neighborhoodAbortRef.current = controller;
    setNeighborhoodReportKey(key);
    setNeighborhoodReport(null);
    setNeighborhoodError('');
    setNeighborhoodLoadingKey(key);
    try {
      const params = new URLSearchParams({ locality: property.locality, city: property.city });
      const response = await fetch(`/api/neighborhood?${params.toString()}`, { signal: controller.signal });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Neighborhood data could not be loaded.');
      if (!controller.signal.aborted) setNeighborhoodReport(data);
    } catch (error) {
      if (error.name !== 'AbortError') setNeighborhoodError(error.message || 'Neighborhood data could not be loaded.');
    } finally {
      if (!controller.signal.aborted) setNeighborhoodLoadingKey('');
    }
  };

  const handleAssistantSubmit = async (event) => {
    event.preventDefault();
    const message = assistantDraft.trim();
    if (!message || assistantBusy) return;

    setAssistantMessages((previous) => [...previous, { role: 'user', text: message }]);
    setAssistantDraft('');
    setAssistantBusy(true);
    try {
      const response = await fetch('/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          city: form.city,
          locality: form.locality,
          max_price: appliedBudget !== '' ? Number(appliedBudget) : Number(budget) || null,
          min_price: Number(appliedMinimumPrice || minimumPrice) || null,
          bhk: appliedFilters.bhk || null,
          resale: appliedFilters.resale,
          area_sqft: appliedFilters.area_sqft,
          area_tolerance: appliedFilters.area_tolerance,
          amenities: appliedFilters.amenities,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Assistant could not search the listings.');
      setAssistantMessages((previous) => [...previous, { role: 'assistant', text: data.answer }]);
      setForm((previous) => ({
        ...previous,
        city: data.filters.city || previous.city,
        locality: data.filters.locality || previous.locality,
        bhk: data.filters.bhk ?? previous.bhk,
        area_sqft: data.filters.area_sqft ?? previous.area_sqft,
        resale: data.filters.resale ?? previous.resale,
        amenities: data.filters.amenities ?? previous.amenities,
      }));
      setAppliedCity(data.filters.city || form.city);
      setAppliedLocality(data.filters.locality || '');
      if (data.filters.max_price != null) {
        const nextBudget = String(data.filters.max_price);
        setBudget(nextBudget);
        setAppliedBudget(nextBudget);
      } else if (data.filters.max_price === null && (data.filters.city || data.filters.locality || data.filters.bhk)) {
        setBudget('');
        setAppliedBudget('');
      }
      const nextMinimumPrice = data.filters.min_price == null ? '' : String(data.filters.min_price);
      setMinimumPrice(nextMinimumPrice);
      setAppliedMinimumPrice(nextMinimumPrice);
      setSearchPriceError('');
      setAppliedFilters({
        bhk: data.filters.bhk ?? null,
        resale: data.filters.resale ?? null,
        area_sqft: data.filters.area_sqft ?? null,
        area_tolerance: data.filters.area_tolerance ?? 0.2,
        amenities: data.filters.amenities || '',
      });
      setHasSearched(true);
      setListingPage(0);
      setSelectedPropertyId('');
      setResult(null);
      document.getElementById('listings')?.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
      setAssistantMessages((previous) => [...previous, { role: 'assistant', text: error.message || 'Search failed. Please try again.' }]);
    } finally {
      setAssistantBusy(false);
    }
  };

  const handleBudgetTradeoff = (filters) => {
    setListingPage(0);
    setAppliedCity(filters.city || form.city);
    setAppliedLocality(Object.hasOwn(filters, 'locality') ? filters.locality || '' : form.locality);
    const nextBudget = filters.max_price == null ? '' : String(filters.max_price);
    const nextMinimumPrice = filters.min_price == null ? '' : String(filters.min_price);
    setBudget(nextBudget);
    setAppliedBudget(nextBudget);
    setMinimumPrice(nextMinimumPrice);
    setAppliedMinimumPrice(nextMinimumPrice);
    setAppliedFilters({
      bhk: filters.bhk,
      resale: filters.resale,
      area_sqft: filters.area_sqft,
      area_tolerance: filters.area_tolerance ?? 0.2,
      amenities: filters.amenities || '',
    });
    setForm((previous) => ({
      ...previous,
      city: filters.city || previous.city,
      locality: Object.hasOwn(filters, 'locality') ? filters.locality || '' : previous.locality,
      bhk: filters.bhk ?? previous.bhk,
      resale: filters.resale == null ? '' : filters.resale,
      area_sqft: filters.area_sqft ?? previous.area_sqft,
      amenities: filters.amenities || '',
    }));
    setSelectedPropertyId('');
    setResult(null);
    setHasSearched(true);
    document.getElementById('listings')?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSignOut = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    setSignedInUser(null);
    setAuthMessage('');
  };

  const fairScore = useMemo(() => {
    if (!result || !result.predicted_price || Number(form.listing_price) <= 0) return 0;
    const delta = Math.abs(Number(form.listing_price) - result.predicted_price);
    const ratio = delta / Math.max(result.predicted_price, 1);
    if (ratio < 0.08) return 92;
    if (ratio < 0.15) return 74;
    return 46;
  }, [form.listing_price, result]);

  const renderPropertyCard = (property, index, isAlternative = false) => {
    const propertyImage = getPropertyCardImage(property, index + 1);
    const selected = selectedPropertyId === property.property_id;
    const neighborhoodKey = `${property.property_id}:${property.locality}:${property.city}`;
    const reportOpen = neighborhoodReportKey === neighborhoodKey;
    return (
      <article key={property.property_id} className={`property-card${selected ? ' property-card--selected' : ''}`}>
        <div className="card-image-wrap">
          <img src={propertyImage} alt={`Illustrative home image for ${property.locality}, ${property.city}`} loading="lazy" decoding="async" />
          <span className="card-tag">{Number(property.resale) ? 'Pre-owned home' : 'New home'}</span>
          {isAlternative && <span className="card-tag card-tag--alt">Alternative match</span>}
          <span className="card-score">Illustrative photo</span>
        </div>
        <div className="card-body">
          <div className="card-header-row">
            <h4 className="property-name">{getPropertyName(property)}</h4>
          </div>
          <div className="card-price-row">
            <strong>{formatCurrency(property.listing_price || property.actual_price || 0)}</strong>
            <span className="property-meta">{formatCurrency(property.price_per_sqft)} per square foot</span>
          </div>
          {Number(property.price_vs_city_bhk_median_percent) > 300 && (
            <p className="listing-price-warning" role="note">
              Asking price is far above the city {property.bhk}-BHK benchmark; verify the price and property details.
            </p>
          )}
          {Number.isFinite(Number(property.price_vs_city_bhk_median_percent)) && (
            <p
              className={`value-insight${property.price_vs_city_bhk_median_percent < -2 ? ' value-insight--below' : property.price_vs_city_bhk_median_percent > 2 ? ' value-insight--above' : ''}`}
              title={`Compared with the city-level ${property.bhk}-BHK median price per square foot`}
            >
              {Math.abs(property.price_vs_city_bhk_median_percent) <= 2
                ? 'Around the city average'
                : `${Math.round(Math.abs(property.price_vs_city_bhk_median_percent))}% ${property.price_vs_city_bhk_median_percent < 0 ? 'below' : 'above'} the city ${property.bhk}-BHK median`}
            </p>
          )}
          <p className="property-location">{property.locality}, {property.city}</p>
          <button
            className="property-map-link"
            type="button"
            onClick={() => openAreaMap(property)}
          >View this area on Google Maps</button>
          <div className="locality-explorer">
            <span className="locality-explorer-title">Explore nearby</span>
            <div className="locality-explorer-links">
              {nearbySearches.map(([label, placeType]) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => openMapPanel(`${placeType} near ${property.locality}, ${property.city}`, `${label} near ${property.locality}`)}
                >{label}</button>
              ))}
            </div>
          </div>
          {getLifestyleHighlights(property).length > 0 && (
            <div className="lifestyle-highlights">
              <span className="locality-explorer-title">Home highlights</span>
              <div className="lifestyle-highlight-list">
                {getLifestyleHighlights(property).map((highlight) => <span key={highlight}>{highlight}</span>)}
              </div>
            </div>
          )}
          <button
            className="neighborhood-toggle"
            type="button"
            aria-expanded={reportOpen}
            onClick={() => handleNeighborhoodExplore(property)}
          >
            {neighborhoodLoadingKey === neighborhoodKey
              ? 'Calculating amenity distances…'
              : reportOpen
              ? 'Hide amenity distances'
              : 'Explore neighbourhood & amenity distances'}
          </button>
          {reportOpen && (
            <div className="neighborhood-report" aria-live="polite">
              {neighborhoodLoadingKey === neighborhoodKey ? (
                <div className="neighborhood-loading-state">
                  <span className="neighborhood-spinner"></span>
                  <p className="neighborhood-status">
                    Calculating distances to schools, healthcare, transit & markets from {property.locality}…
                  </p>
                </div>
              ) : neighborhoodError ? (
                <div className="neighborhood-error-state">
                  <p className="neighborhood-status neighborhood-status--error">
                    {neighborhoodError}
                  </p>
                  <button
                    className="neighborhood-retry-btn"
                    type="button"
                    onClick={() => handleNeighborhoodExplore(property, true)}
                  >
                    Try again
                  </button>
                </div>
              ) : neighborhoodReport ? (
                <AmenityDistanceExplorer property={property} report={neighborhoodReport} />
              ) : null}
            </div>
          )}
          <div className="card-features">
            <span>{property.area_sqft} sq. ft.</span>
            <span>{property.bhk} BHK</span>
            <span>{Number(property.resale) ? 'Pre-owned home' : 'New home'}</span>
            <span>Listing {property.property_id}</span>
            {(property.amenities || '').split(',').map((amenity) => amenity.trim()).filter(Boolean).map((amenity) => (
              <span key={amenity}>{formatFeatureLabel(amenity)}</span>
            ))}
          </div>
          <button className="secondary-btn listing-select-btn" type="button" onClick={() => handleUseListing(property)}>
            {selected ? 'Selected · ready to estimate' : 'Use this home'}
          </button>
        </div>
      </article>
    );
  };

  return (
    <div className="page-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark" aria-label="MakaanX logo">
            <svg viewBox="0 0 64 64" role="img" aria-hidden="true">
              <path d="M16 31L32 18L48 31" stroke="#24776e" strokeWidth="4.2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M21 29V42.5C21 43.9 22.1 45 23.5 45H40.5C41.9 45 43 43.9 43 42.5V29" stroke="#24776e" strokeWidth="3.8" strokeLinejoin="round" fill="none" />
              <path d="M28 30L32 34L36 30" stroke="#d97438" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M27 45V38H37V45" stroke="#d97438" strokeWidth="3.1" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <h1>MakaanX</h1>
            <span>Home search and price estimates</span>
          </div>
        </div>
        <nav className="nav">
          <a href="#discover">Discover</a>
          <a href="#predict">Estimate</a>
          <a href="#listings">Homes</a>
        </nav>
        <div className="account-actions">
          {signedInUser ? (
            <>
              <span className="account-name">{signedInUser.name}</span>
              <button className="secondary-btn history-btn" type="button" onClick={() => setHistoryOpen(true)}>
                History{predictionHistory.length ? ` (${predictionHistory.length})` : ''}
              </button>
              <button className="secondary-btn signout-btn" type="button" onClick={handleSignOut}>Sign out</button>
            </>
          ) : (
            <button className="secondary-btn signin-btn"
              type="button"
              onClick={() => { setAuthMessage(''); setAuthMode('signin'); setAuthOpen(true); }}
            >
              Sign in / Register
            </button>
          )}
        </div>
      </header>

      <main className="content-wrapper listing-shell" id="discover">
        <section className="hero listing-hero">
          <div className="hero-copy">
            <p className="eyebrow">Find your next home</p>
            <h2>Find a home, then check its estimated price.</h2>
            <p>
              Choose your city, budget, and home features to see matching homes and a price estimate.
            </p>
            <div className="hero-search" id="search">
              <div className="search-tabs">
                <span className="search-tab active">Buy</span>
              </div>
              <div className="search-bar">
                <label className="search-field">
                  <span>City</span>
                  <select name="city" value={form.city} onChange={handleChange}>
                    {cityOptions.map((city) => <option key={city} value={city}>{city}</option>)}
                  </select>
                </label>
                <label className="search-field">
                  <span>Area</span>
                  <select name="locality" value={form.locality} onChange={handleChange}>
                    <option value="">Any area in {form.city}</option>
                    {availableLocalities.map((locality) => <option key={locality} value={locality}>{locality}</option>)}
                  </select>
                </label>
                <label className="search-field" htmlFor="search-budget">
                  <div className="search-field-title-row">
                    <span>Max budget</span>
                    <strong className="budget-indicator-tag">{formatBudgetFriendly(budget)}</strong>
                  </div>
                  <input
                    id="search-budget"
                    type="number"
                    min="0"
                    step="500000"
                    value={budget}
                    onChange={(event) => {
                      setBudget(event.target.value);
                      setSearchPriceError('');
                    }}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(); }}
                    placeholder="e.g. 30000000 (3 Cr)"
                  />
                </label>
                <label className="search-field">
                  <span>BHK</span>
                  <select name="bhk" value={form.bhk} onChange={handleChange}>
                    <option value="">Any BHK</option>
                    {[1, 2, 3, 4, 5].map((bhk) => <option key={bhk} value={bhk}>{bhk} BHK</option>)}
                  </select>
                </label>
                <button className="primary-btn search-btn" type="button" onClick={handleSearch}>Find matching homes</button>
              </div>

              <div className="budget-presets-bar">
                <span className="budget-presets-label">Quick Budget:</span>
                {[
                  { label: '₹50 Lakh', value: '5000000' },
                  { label: '₹1 Crore', value: '10000000' },
                  { label: '₹2 Crore', value: '20000000' },
                  { label: '₹3 Crore', value: '30000000' },
                  { label: '₹5 Crore', value: '50000000' },
                  { label: 'No limit', value: '' },
                ].map((preset) => {
                  const active = budget.trim() === preset.value;
                  return (
                    <button
                      key={preset.label}
                      type="button"
                      className={`budget-preset-pill ${active ? 'is-active' : ''}`}
                      onClick={() => {
                        setBudget(preset.value);
                        setMinimumPrice('');
                        setAppliedBudget(preset.value);
                        setAppliedMinimumPrice('');
                        setSearchPriceError('');
                        setListingPage(0);
                        setHasSearched(true);
                      }}
                    >
                      {preset.label}
                    </button>
                  );
                })}
              </div>
              {searchPriceError && <p className="search-price-error" role="alert">{searchPriceError}</p>}
              <details className="search-preferences">
                <summary>More filters</summary>
                <div className="search-preference-fields">
                  <label>
                    Home size (sq. ft.)
                    <input type="number" min="200" step="50" name="area_sqft" value={form.area_sqft} onChange={handleChange} />
                  </label>
                  <label>
                    Home type
                    <select name="resale" value={form.resale} onChange={handleChange}>
                      <option value="">Any</option>
                      <option value="0">New home</option>
                      <option value="1">Resale home</option>
                    </select>
                  </label>
                  <div className="search-amenities">
                    <span>Home features</span>
                    <div className="amenity-options">
                      {amenityOptions.map((amenity) => (
                        <label key={amenity}>
                          <input
                            type="checkbox"
                            checked={form.amenities.split(',').includes(amenity)}
                            onChange={(event) => {
                              const selected = form.amenities.split(',').filter(Boolean);
                              const next = event.target.checked ? [...selected, amenity] : selected.filter((item) => item !== amenity);
                              setForm((previous) => ({ ...previous, amenities: next.join(',') }));
                              setSelectedPropertyId('');
                              setResult(null);
                            }}
                          />
                          {formatFeatureLabel(amenity)}
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              </details>
            </div>
          </div>
        </section>

        <nav className="workflow-steps" aria-label="Property search workflow">
          <a className={workflowStep === 1 ? 'workflow-step is-current' : 'workflow-step is-complete'} href="#search">
            <span>01</span><strong>Search</strong><small>Set city and budget</small>
          </a>
          <a className={`workflow-step workflow-step-choose${workflowStep === 2 ? ' is-current' : workflowStep > 2 ? ' is-complete' : ''}`} href="#listings">
            <span>02</span><strong>Choose</strong><small>Compare homes that fit</small>
          </a>
          <a className={`workflow-step workflow-step-estimate${workflowStep === 3 ? ' is-current' : ''}`} href="#predict">
            <span>03</span><strong>Estimate</strong><small>See the estimated price</small>
          </a>
        </nav>

        {budgetCoach && (budgetCoach.comparable_homes > 0 || budgetCoach.tradeoffs?.length > 0) && (
          <section className="budget-coach" aria-live="polite">
            <div className="budget-coach-summary">
              <p className="step-kicker">{budgetCoach.comparable_homes > 0 ? 'BUDGET CHECK' : 'FILTER SUGGESTIONS'}</p>
              {budgetCoach.comparable_homes > 0 && (appliedBudget !== '' || appliedMinimumPrice !== '') ? (
                <>
                  <h2>{budgetCoach.budget_fit_percent}% of similar homes fit your price range</h2>
                  <p>{budgetCoach.within_budget.toLocaleString()} of {budgetCoach.comparable_homes.toLocaleString()} homes match your choices and price range.</p>
                  {budgetCoach.median_comparable_price && (
                    <strong className="budget-typical-price">Typical price for these homes: {formatCurrency(budgetCoach.median_comparable_price)}</strong>
                  )}
                  <div className="budget-fit-track" role="progressbar" aria-label="Homes within budget" aria-valuenow={budgetCoach.budget_fit_percent} aria-valuemin="0" aria-valuemax="100">
                    <span style={{ width: `${budgetCoach.budget_fit_percent}%` }} />
                  </div>
                </>
              ) : budgetCoach.comparable_homes > 0 ? (
                <p>Enter a budget to see how many similar homes fit.</p>
              ) : (
                <>
                  <h2>No homes match all these filters</h2>
                  <p>Try one of the filter combinations with available listings.</p>
                </>
              )}
            </div>
            {budgetCoach.tradeoffs?.length > 0 && (
              <div className="budget-tradeoffs">
                <strong>{budgetCoach.comparable_homes > 0 ? 'Need more choices?' : 'Properties are listed with these filters'}</strong>
                {budgetCoach.tradeoffs.slice(0, 3).map((tradeoff) => (
                  <button key={tradeoff.key} type="button" onClick={() => handleBudgetTradeoff(tradeoff.filters)}>
                    <span>
                      {tradeoff.label}
                      <small className="tradeoff-filter-summary">{describeFilters(tradeoff.filters)}</small>
                    </span>
                    <small>{tradeoff.additional_homes.toLocaleString()} homes</small>
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        <section className="panel property-grid workflow-listings" id="listings">
          <div className="section-header property-header">
            <div>
              <p className="step-kicker">STEP 2 OF 3 · CHOOSE A HOME</p>
              <h3>Matching listings</h3>
              <p className="listing-filter-summary">
                {hasSearched
                  ? `Results for your preferences: ${describeFilters({
                    city: appliedCity,
                    locality: appliedLocality,
                    bhk: appliedFilters.bhk,
                    min_price: appliedMinimumPrice !== '' ? Number(appliedMinimumPrice) : null,
                    max_price: appliedBudget !== '' ? Number(appliedBudget) : null,
                    area_sqft: appliedFilters.area_sqft,
                    resale: appliedFilters.resale,
                    amenities: appliedFilters.amenities,
                  })}`
                  : `Choose your preferences, then find matching ${form.bhk} BHK homes in ${form.locality || form.city}.`}
              </p>
            </div>
              <span className="property-meta">{totalProperties.toLocaleString()} homes available</span>
          </div>

          <div className="cards-row">
            {propertySuggestions.length ? (
              propertySuggestions.map((property, index) => renderPropertyCard(property, index))
            ) : (
              <div className="no-exact-matches-block">
                <div className="no-matches-callout">
                  <div className="no-matches-icon">🏠</div>
                  <div className="no-matches-info">
                    <h4>
                      No {appliedFilters.bhk ? `${appliedFilters.bhk} BHK ` : ''}properties found {Number(appliedMinimumPrice) > 0
                        ? `between ${formatBudgetFriendly(appliedMinimumPrice)} and ${appliedBudget ? formatBudgetFriendly(appliedBudget) : 'any price'}`
                        : `strictly under ${appliedBudget ? formatBudgetFriendly(appliedBudget) : 'your limit'}`} in {appliedLocality || appliedCity}
                    </h4>
                    <p>
                      {appliedLocality
                        ? `We found no listings in ${appliedLocality} matching all current filters ${Number(appliedMinimumPrice) > 0 ? 'within this price range' : `under ${appliedBudget ? formatBudgetFriendly(appliedBudget) : 'this budget'}`}. Check out the alternative options below:`
                        : `Try exploring homes across all of ${appliedCity} or relaxing the BHK and size filters.`}
                    </p>
                    <div className="no-matches-actions">
                      {appliedLocality && Number(appliedMinimumPrice) === 0 && (
                        <button
                          type="button"
                          className="quick-fix-btn"
                          onClick={() => {
                            setAppliedLocality('');
                            setForm((prev) => ({ ...prev, locality: '' }));
                            setListingPage(0);
                          }}
                        >
                          🏙️ View all homes under {appliedBudget ? formatBudgetFriendly(appliedBudget) : 'budget'} in {appliedCity}
                        </button>
                      )}
                      {(appliedBudget !== '' || appliedMinimumPrice !== '') && (
                        <button
                          type="button"
                          className="quick-fix-btn"
                          onClick={() => {
                            setBudget('');
                            setMinimumPrice('');
                            setAppliedBudget('');
                            setAppliedMinimumPrice('');
                            setListingPage(0);
                          }}
                        >
                          💰 {appliedMinimumPrice !== '' ? 'Clear price range' : 'View all homes'} in {appliedLocality || appliedCity} (no budget limit)
                        </button>
                      )}
                      {(appliedFilters.bhk || appliedFilters.resale !== null || appliedFilters.area_sqft) && (
                        <button
                          type="button"
                          className="quick-fix-btn"
                          onClick={() => {
                            setForm((prev) => ({ ...prev, bhk: '', resale: '', area_sqft: '' }));
                            setAppliedFilters({ bhk: null, resale: null, area_sqft: null, area_tolerance: 0.2, amenities: '' });
                            setListingPage(0);
                          }}
                        >
                          🔄 Any BHK & Any Home Size
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {fallbackProperties.length > 0 && (
                  <div className="fallback-listings-container">
                    <div className="fallback-listings-header">
                      <h5>
                        {fallbackMode === 'locality_all'
                          ? `Available listings in ${appliedLocality} (sorted lowest price first):`
                          : `Available listings under ${formatBudgetFriendly(appliedBudget)} across ${appliedCity}:`}
                      </h5>
                      <span className="fallback-badge">Alternative Matches</span>
                    </div>
                    <div className="cards-row">
                      {fallbackProperties.map((property, index) => renderPropertyCard(property, index, true))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
          {totalProperties > listingPageSize && (
            <nav className="listing-pagination" aria-label="Property result pages">
              <span>
                Showing {listingPage * listingPageSize + 1}–{Math.min((listingPage + 1) * listingPageSize, totalProperties)} of {totalProperties.toLocaleString()} matching homes
              </span>
              <div className="listing-pagination-controls">
                <button type="button" disabled={listingPage === 0} onClick={() => setListingPage((page) => Math.max(0, page - 1))}>Previous</button>
                <span>Page {listingPage + 1} of {Math.ceil(totalProperties / listingPageSize).toLocaleString()}</span>
                <button type="button" disabled={(listingPage + 1) * listingPageSize >= totalProperties} onClick={() => setListingPage((page) => page + 1)}>Next</button>
              </div>
            </nav>
          )}
        </section>

        <section className="main-grid listing-main" id="predict">
          <div className="panel form-panel listing-form-panel">
            <div className="section-header">
              <div>
                <p className="step-kicker">STEP 3 OF 3 · ESTIMATED PRICE</p>
                <h3>Your home details</h3>
              </div>
              <span className="pill">Price estimate</span>
            </div>

            <div className="estimate-context">
              <button
                className="estimate-location-link"
                type="button"
                onClick={() => openMapPanel(`${form.locality || form.city}, ${form.city}`, `${form.locality || form.city}, ${form.city}`)}
                aria-label={`Open ${form.locality || form.city}, ${form.city} in Google Maps`}
              >
                {form.locality || 'Choose an area'}, {form.city} ↗
              </button>
              {selectedPropertyId && <span>Home selected</span>}
            </div>

            <div className="form-grid">
              <label>
                Area
                <select name="locality" value={form.locality} onChange={handleChange}>
                  <option value="">Choose an area in {form.city}</option>
                  {availableLocalities.map((loc) => (
                    <option key={loc} value={loc}>{loc}</option>
                  ))}
                </select>
              </label>
              <label>
                BHK
                <input type="number" min="1" max="9" name="bhk" value={form.bhk} onChange={handleChange} />
              </label>
              <label>
                Home size (square feet)
                <input type="number" min="200" name="area_sqft" value={form.area_sqft} onChange={handleChange} />
              </label>
              <label>
                Home type
                <select name="resale" value={form.resale} onChange={handleChange}>
                  <option value="0">New home</option>
                  <option value="1">Pre-owned home</option>
                </select>
              </label>
              <label className="wide-field">
                Listed price (optional)
                <input type="number" min="0" name="listing_price" value={form.listing_price} onChange={handleChange} placeholder="For price comparison" />
              </label>
            </div>

            <fieldset className="amenity-fieldset">
              <legend>Home features</legend>
              <div className="amenity-options">
                {amenityOptions.map((amenity) => (
                  <label key={amenity}>
                    <input
                      type="checkbox"
                      value={amenity}
                      checked={form.amenities.split(',').includes(amenity)}
                      onChange={(event) => {
                        const selected = form.amenities.split(',').filter(Boolean);
                        const next = event.target.checked
                          ? [...selected, amenity]
                          : selected.filter((value) => value !== amenity);
                        setForm((previous) => ({ ...previous, amenities: next.join(',') }));
                        setSelectedPropertyId('');
                        setResult(null);
                      }}
                    />
                    {formatFeatureLabel(amenity)}
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="action-row">
              <button className="primary-btn" onClick={() => handlePredict()} disabled={predicting}>
                {predicting ? 'Calculating estimate…' : 'Estimate this home'}
              </button>
            </div>
          </div>

          <div className="panel result-panel prediction-panel">
            <div className="section-header">
              <h3>Your estimate</h3>
              <span className={`pill ${result ? 'success' : ''}`}>{predicting ? 'Calculating…' : result ? 'Ready' : selectedPropertyId ? 'Ready to estimate' : 'Pending'}</span>
            </div>

            <div className="prediction-price-box">
              <span>Estimated price</span>
              <strong>{predicting ? 'Calculating estimate…' : result ? formatCurrency(activePrediction.predicted_price) : '—'}</strong>
              {!result && !predicting && (
                <span className="estimate-pending-note">
                  {selectedPropertyId
                    ? 'Home selected. Click “Estimate this home” to calculate its price.'
                    : 'Select a home, then click “Estimate this home”.'}
                </span>
              )}
              {result && activePrediction.estimated_range?.upper > 0 && (
                <button className="estimate-range-search-btn" type="button" onClick={handleSearchEstimateRange}>
                  Find homes in this estimated price range
                </button>
              )}
              {predictError && (
                <p className="auth-inline-message" role="alert" style={{ margin: '8px 0 0' }}>{predictError}</p>
              )}
            </div>

            <div className="result-metric-row small">
              <div>
                <span>Price per square foot</span>
                <strong>{result ? formatCurrency(activePrediction.price_per_sqft) : '—'}</strong>
              </div>
              <div>
                <span>Comparable listings</span>
                <strong>{result ? activePrediction.comparable_count : '—'}</strong>
              </div>
            </div>

            <div className="feature-badges">
              <span>{form.bhk} BHK</span>
              <span>{form.area_sqft} sq. ft.</span>
              <span>{Number(form.resale) ? 'Pre-owned home' : 'New home'}</span>
              {form.amenities.split(',').filter(Boolean).map((amenity) => <span key={amenity}>{formatFeatureLabel(amenity)}</span>)}
            </div>

            <div className="explain-box">
              <h4>What affects this estimate?</h4>
              {result && activePrediction.explanation?.summary ? (
                <p>{activePrediction.explanation.summary}</p>
              ) : result && activePrediction.explanation?.top_factors?.length ? (
                <ul>
                  {activePrediction.explanation.top_factors.map((factor) => (
                    <li key={factor.feature}>{formatFeatureLabel(factor.feature)} · {Math.round(factor.weight * 100)}%</li>
                  ))}
                </ul>
              ) : (
                <p className="empty-state-text">Choose a home and select “Estimate this home” to see its price.</p>
              )}
            </div>

          </div>
        </section>

      </main>
      <div className={`auth-overlay${authOpen ? ' auth-overlay--open' : ''}`} aria-hidden={!authOpen}>
        <section className="auth-page" role="dialog" aria-modal="true" aria-labelledby="auth-title">
          <button className="auth-close" type="button" onClick={() => setAuthOpen(false)} aria-label="Close sign in">×</button>
          <div className="auth-story">
            <div className="auth-story-brand"><span className="auth-story-mark">⌂</span> MakaanX</div>
            <div className="auth-story-copy">
              <p className="eyebrow">A clearer way home</p>
              <h2>Find a place that feels right.</h2>
              <p>Explore homes, understand local areas, and get a price estimate tailored to the details that matter to you.</p>
              <div className="auth-benefits">
                <span><b>01</b> Homes matched to your needs</span>
                <span><b>02</b> Neighborhood essentials nearby</span>
                <span><b>03</b> Transparent price estimates</span>
              </div>
            </div>
            <span className="auth-story-foot">Your next chapter starts here.</span>
          </div>
          <div className="auth-form-side">
            <div className="auth-form-card">
              <div className="auth-mode-switch" role="tablist" aria-label="Account access">
                <button type="button" role="tab" aria-selected={authMode === 'signin'} className={authMode === 'signin' ? 'active' : ''} onClick={() => { setAuthMode('signin'); setAuthMessage(''); }}>Sign in</button>
                <button type="button" role="tab" aria-selected={authMode === 'register'} className={authMode === 'register' ? 'active' : ''} onClick={() => { setAuthMode('register'); setAuthMessage(''); }}>Create account</button>
              </div>
              <p className="auth-form-eyebrow">{authMode === 'signin' ? 'WELCOME BACK' : 'GET STARTED'}</p>
              <h1 id="auth-title">{authMode === 'signin' ? 'Sign in to MakaanX' : 'Create your account'}</h1>
              <p className="auth-form-description">
                {authMode === 'signin'
                  ? 'Sign in to restore and keep your saved price estimates.'
                  : 'Create an account to save your price estimates and revisit them any time.'}
              </p>
              {authMessage && <p className="auth-inline-message" role="alert">{authMessage}</p>}
              {authLoading && <p className="auth-loading" role="status">Signing you in…</p>}
              {!authLoading && (
                <form className="auth-fields" onSubmit={handleAuthSubmit}>
                  {authMode === 'register' && (
                    <label>
                      Name
                      <input
                        autoComplete="name"
                        required
                        maxLength={80}
                        value={authForm.name}
                        onChange={(event) => setAuthForm((previous) => ({ ...previous, name: event.target.value }))}
                      />
                    </label>
                  )}
                  <label>
                    Email
                    <input
                      type="email"
                      autoComplete="email"
                      required
                      maxLength={254}
                      value={authForm.email}
                      onChange={(event) => setAuthForm((previous) => ({ ...previous, email: event.target.value }))}
                    />
                  </label>
                  <label>
                    Password
                    <input
                      type="password"
                      autoComplete={authMode === 'signin' ? 'current-password' : 'new-password'}
                      required
                      minLength={8}
                      maxLength={256}
                      value={authForm.password}
                      onChange={(event) => setAuthForm((previous) => ({ ...previous, password: event.target.value }))}
                    />
                    {authMode === 'register' && <small>Use at least 8 characters.</small>}
                  </label>
                  <button className="primary-btn auth-submit-btn" type="submit">
                    {authMode === 'signin' ? 'Sign in' : 'Create account'}
                  </button>
                </form>
              )}
              {googleClientId && (
                <>
                  <div className="auth-divider"><span>OR CONTINUE WITH GOOGLE</span></div>
                  <div
                    id="google-signin-button"
                    className={authLoading ? 'auth-google-button is-loading' : 'auth-google-button'}
                    aria-label="Continue with Google"
                  />
                </>
              )}
              {!googleClientId && !authLoading && (
                <button className="secondary-btn demo-btn" type="button" onClick={handleDemoSignIn}>
                  Continue as Demo Buyer
                </button>
              )}
              <p className="auth-privacy-note">Your estimates are saved privately to your account.</p>
            </div>
            <span className="auth-copyright">© 2026 MakaanX · Home search made more thoughtful</span>
          </div>
        </section>
      </div>
      {historyOpen && signedInUser && (
        <div className="history-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setHistoryOpen(false); }}>
          <section className="history-dialog" role="dialog" aria-modal="true" aria-labelledby="history-title">
            <header className="history-header">
              <div>
                <span>YOUR ACCOUNT</span>
                <h2 id="history-title">Estimate history</h2>
              </div>
              <button className="history-close" type="button" onClick={() => setHistoryOpen(false)} aria-label="Close estimate history">×</button>
            </header>
            {historyLoading ? (
              <p className="history-empty" role="status">Loading your saved estimates…</p>
            ) : historyError ? (
              <p className="auth-inline-message" role="alert">{historyError}</p>
            ) : predictionHistory.length ? (
              <div className="history-list">
                {predictionHistory.map((entry) => (
                  <button className="history-entry" key={entry.id} type="button" onClick={() => handleRestoreHistory(entry)}>
                    <span>{entry.request?.bhk || 'Home'} BHK · {entry.request?.locality || 'Area'}, {entry.request?.city || 'City'}</span>
                    <strong>{formatCurrency(entry.result?.predicted_price || 0)}</strong>
                    <small>{new Date(entry.created_at).toLocaleString()}</small>
                  </button>
                ))}
              </div>
            ) : (
              <p className="history-empty">Your estimates will appear here after you calculate a price while signed in.</p>
            )}
          </section>
        </div>
      )}
      {mapPanel && (
        <div className="map-panel-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) closeMapPanel(); }}>
          <aside className="map-side-panel" role="dialog" aria-modal="true" aria-label={`Map: ${mapPanel.title}`}>
            <header className="map-side-panel-header">
              <div><span>MAP EXPLORER</span><strong>{mapPanel.title}</strong></div>
              {mapPanel.googleMapsUrl && (
                <a className="map-side-panel-open-link" href={mapPanel.googleMapsUrl} target="_blank" rel="noopener noreferrer">
                  Open in Google Maps ↗
                </a>
              )}
              <button type="button" className="map-side-panel-close" onClick={closeMapPanel} aria-label="Close map">×</button>
            </header>
            {mapPanel.loading ? (
              <p className="map-side-panel-status" role="status">Finding this area…</p>
            ) : (
              <>
                {mapPanel.notice && <p className="map-side-panel-notice" role="status">{mapPanel.notice}</p>}
                <iframe
                  className="map-side-panel-frame"
                  title={`Google Maps for ${mapPanel.title}`}
                  src={getGoogleMapsEmbedUrl(mapPanel.query)}
                  loading="eager"
                  allowFullScreen
                  referrerPolicy="no-referrer-when-downgrade"
                />
              </>
            )}
          </aside>
        </div>
      )}
      <aside className={`assistant-widget${assistantOpen ? ' assistant-widget--open' : ''}`}>
        {assistantOpen && (
          <section className="assistant-panel" aria-label="Home finder">
            <header className="assistant-header">
              <div><strong>Home finder</strong><span>Find homes from your search</span></div>
              <button className="assistant-close" type="button" onClick={() => setAssistantOpen(false)} aria-label="Close assistant">×</button>
            </header>
            <div className="assistant-messages" aria-live="polite">
              {assistantMessages.map((entry, index) => (
                <p className={`assistant-message assistant-message--${entry.role}`} key={`${entry.role}-${index}`}>{entry.text}</p>
              ))}
                    {assistantBusy && <p className="assistant-typing" role="status">Looking for homes…</p>}
            </div>
            <form className="assistant-form" onSubmit={handleAssistantSubmit}>
              <input
                aria-label="Ask about properties"
                value={assistantDraft}
                onChange={(event) => setAssistantDraft(event.target.value)}
                placeholder="e.g. 2 bedrooms under 1 crore in Mumbai"
              />
              <button className="primary-btn" type="submit" disabled={assistantBusy || !assistantDraft.trim()}>Send</button>
            </form>
          </section>
        )}
        <button className="assistant-launcher" type="button" onClick={() => setAssistantOpen((open) => !open)}>
          {assistantOpen ? 'Close assistant' : 'Ask MakaanX'}
        </button>
      </aside>
    </div>
  );
}

export default App;
