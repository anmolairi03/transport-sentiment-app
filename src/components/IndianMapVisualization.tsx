import React from 'react';
import { StateData } from '../types';
import { getSentimentColor, getSentimentEmoji } from '../utils/sentimentAnalysis';
import { INDIAN_STATES } from '../utils/indianStatesData';
import indiaStatesData from '../assets/india_states.json';

interface IndianMapVisualizationProps {
  states: StateData[];
  selectedTransportType: string;
}

export const IndianMapVisualization: React.FC<IndianMapVisualizationProps> = ({ 
  states, 
  selectedTransportType 
}) => {
  const filteredStates = states.filter(state => 
    selectedTransportType === 'all' || 
    state.transportBreakdown[selectedTransportType as keyof typeof state.transportBreakdown] > 0
  );

  // Get the bounds of India from the GeoJSON data
  const getBounds = () => {
    let minLat = Infinity, maxLat = -Infinity;
    let minLng = Infinity, maxLng = -Infinity;

    indiaStatesData.features.forEach((feature: any) => {
      if (feature.geometry.type === 'Polygon') {
        feature.geometry.coordinates[0].forEach((coord: [number, number]) => {
          const [lng, lat] = coord;
          minLat = Math.min(minLat, lat);
          maxLat = Math.max(maxLat, lat);
          minLng = Math.min(minLng, lng);
          maxLng = Math.max(maxLng, lng);
        });
      } else if (feature.geometry.type === 'MultiPolygon') {
        feature.geometry.coordinates.forEach((polygon: any) => {
          polygon[0].forEach((coord: [number, number]) => {
            const [lng, lat] = coord;
            minLat = Math.min(minLat, lat);
            maxLat = Math.max(maxLat, lat);
            minLng = Math.min(minLng, lng);
            maxLng = Math.max(maxLng, lng);
          });
        });
      }
    });

    return { minLat, maxLat, minLng, maxLng };
  };

  const bounds = getBounds();
  const mapWidth = 800;
  const mapHeight = 600;

  // Convert lat/lng to SVG coordinates
  const projectCoordinate = (lng: number, lat: number) => {
    const x = ((lng - bounds.minLng) / (bounds.maxLng - bounds.minLng)) * mapWidth;
    const y = ((bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat)) * mapHeight;
    return [x, y];
  };

  // Convert polygon coordinates to SVG path
  const coordinatesToPath = (coordinates: any) => {
    if (!coordinates || coordinates.length === 0) return '';
    
    const pathCommands = coordinates.map((coord: [number, number]) => {
      const [lng, lat] = coord;
      const [x, y] = projectCoordinate(lng, lat);
      return `${x},${y}`;
    }).join(' L ');
    
    return `M ${pathCommands} Z`;
  };

  // Get state data for coloring
  const getStateData = (stateName: string) => {
    return filteredStates.find(state => 
      state.state === stateName || 
      state.state.toLowerCase().includes(stateName.toLowerCase()) ||
      stateName.toLowerCase().includes(state.state.toLowerCase())
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">India Transport Sentiment Map</h2>
        <div className="text-sm text-gray-600">
          Real-time sentiment analysis across Indian states
        </div>
      </div>
      
      {/* SVG Map Container */}
      <div className="relative bg-gradient-to-br from-blue-50 to-green-50 rounded-lg overflow-hidden">
        <svg 
          width="100%" 
          height="500" 
          viewBox={`0 0 ${mapWidth} ${mapHeight}`}
          className="w-full h-[500px]"
        >
          {/* State boundaries */}
          {indiaStatesData.features.map((feature: any, index: number) => {
            const stateName = feature.properties.NAME_1 || feature.properties.name || feature.properties.ST_NM;
            const stateData = getStateData(stateName);
            
            let pathData = '';
            
            if (feature.geometry.type === 'Polygon') {
              pathData = coordinatesToPath(feature.geometry.coordinates[0]);
            } else if (feature.geometry.type === 'MultiPolygon') {
              pathData = feature.geometry.coordinates
                .map((polygon: any) => coordinatesToPath(polygon[0]))
                .join(' ');
            }

            const fillColor = stateData 
              ? getSentimentColor(stateData.sentimentScore)
              : '#3B82F6'; // Blue color for states with no data

            return (
              <g key={index}>
                <path
                  d={pathData}
                  fill={fillColor}
                  stroke="#ffffff"
                  strokeWidth="1"
                  opacity={stateData ? "0.8" : "0.6"}
                  className="hover:opacity-100 transition-opacity cursor-pointer"
                />
              </g>
            );
          })}

          {/* Data points for states with data */}
          {filteredStates.map((state) => {
            const stateCoords = INDIAN_STATES[state.state];
            if (!stateCoords) return null;

            const [x, y] = projectCoordinate(stateCoords.lng, stateCoords.lat);
            const score = Number(state.sentimentScore || 0);

            return (
              <g key={state.state}>
                {/* Heatmap Circle */}
                <circle
                  cx={x}
                  cy={y}
                  r={15 + Math.abs(score) * 10}
                  fill={getSentimentColor(score)}
                  opacity="0.4"
                  className="animate-pulse"
                />

                {/* Data Point */}
                <circle
                  cx={x}
                  cy={y}
                  r="8"
                  fill={getSentimentColor(score)}
                  stroke="white"
                  strokeWidth="2"
                  className="cursor-pointer hover:r-10 transition-all"
                />

                {/* Emoji Indicator */}
                <text
                  x={x}
                  y={y + 2}
                  textAnchor="middle"
                  fontSize="10"
                  className="pointer-events-none"
                >
                  {getSentimentEmoji({
                    polarity: score,
                    subjectivity: 0.5,
                    label: 'neutral',
                    confidence: 0.8,
                  })}
                </text>

                {/* Tooltip Group */}
                <g className="opacity-0 hover:opacity-100 transition-opacity pointer-events-none">
                  <rect
                    x={x + 15}
                    y={y - 40}
                    width="200"
                    height="80"
                    fill="rgba(0, 0, 0, 0.9)"
                    rx="4"
                    ry="4"
                  />
                  <text x={x + 25} y={y - 25} fill="white" fontSize="12" fontWeight="bold">
                    {state.state}
                  </text>
                  <text x={x + 25} y={y - 10} fill="white" fontSize="10">
                    Sentiment: {typeof state.sentimentScore === 'number'
                      ? state.sentimentScore.toFixed(2)
                      : !isNaN(Number(state.sentimentScore))
                        ? Number(state.sentimentScore).toFixed(2)
                        : 'N/A'}
                  </text>
                  <text x={x + 25} y={y + 5} fill="white" fontSize="10">
                    Messages: {state.totalMessages.toLocaleString()}
                  </text>
                  <text x={x + 25} y={y + 20} fill="white" fontSize="10">
                    Trend: {state.trend}
                  </text>
                </g>
              </g>
            );
          })}
        </svg>

        {/* Regional Labels */}
        <div className="absolute top-4 left-4 text-xs text-gray-600 bg-white/80 p-2 rounded">
          <div className="font-semibold mb-1">Regions</div>
          <div>🔵 North • 🟢 South • 🟡 East • 🟠 West • 🟣 Central</div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-green-500"></div>
            <span className="text-sm">Positive Sentiment</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-yellow-500"></div>
            <span className="text-sm">Neutral Sentiment</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-red-500"></div>
            <span className="text-sm">Negative Sentiment</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 rounded-full bg-blue-500"></div>
            <span className="text-sm">No Data</span>
          </div>
        </div>
        <div className="text-sm text-gray-500">
          Total States: {filteredStates.length} | 
          Last Updated: {new Date().toLocaleTimeString('en-IN')}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="mt-4 grid grid-cols-5 gap-4 text-center">
        {['north', 'south', 'east', 'west', 'central'].map(region => {
          const regionStates = filteredStates.filter(s => INDIAN_STATES[s.state]?.region === region);
          const avgSentiment = regionStates.length > 0 
            ? regionStates.reduce((sum, s) => sum + Number(s.sentimentScore || 0), 0) / regionStates.length
            : 0;
          
          return (
            <div key={region} className="bg-gray-50 p-3 rounded-lg">
              <div className="text-lg font-bold" style={{ color: getSentimentColor(avgSentiment) }}>
                {regionStates.length}
              </div>
              <div className="text-xs text-gray-600 capitalize">{region}</div>
              <div className="text-xs font-medium" style={{ color: getSentimentColor(avgSentiment) }}>
                {avgSentiment.toFixed(2)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};