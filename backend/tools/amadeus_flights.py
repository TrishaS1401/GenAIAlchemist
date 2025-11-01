"""Amadeus API integration for flight search and booking.

This module provides the service class and agent-callable tool functions
for interacting with the Amadeus Flight Search APIs.
"""

import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import requests
from google.adk.tools import ToolContext


# --- Service Class for Amadeus API Interaction ---

class AmadeusFlightsService:
    """
    Service class to handle all interactions with the Amadeus Flight APIs.
    Manages API credentials, authentication (OAuth2), and request execution.
    """

    def __init__(self):
        """Initializes the Amadeus service, loading credentials from environment variables."""
        self.api_key = os.getenv("AMADEUS_CLIENT_ID")
        self.api_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        self.base_url = "https://test.api.amadeus.com"  # Use production URL for live data
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

        if not self.api_key or not self.api_secret:
            raise ValueError("AMADEUS_API_KEY and AMADEUS_API_SECRET environment variables must be set.")

    def _get_access_token(self) -> str:
        """
        Retrieves a new OAuth2 access token from Amadeus if the current one is
        missing or expired. Caches the token for reuse.
        """
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token

        url = f"{self.base_url}/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret
        }

        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 1799)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

            return self.access_token
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get Amadeus access token: {e}")

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Makes an authenticated GET request to a specified Amadeus API endpoint.
        """
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        full_url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(full_url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_details = e.response.text if e.response else "No response from server"
            raise Exception(f"Amadeus API request to {endpoint} failed: {e}. Details: {error_details}")

    def _make_post_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Makes an authenticated POST request to a specified Amadeus API endpoint.
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.amadeus+json"
        }
        full_url = f"{self.base_url}{endpoint}"

        try:
            response = requests.post(full_url, headers=headers, json=payload, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            error_details = e.response.text if e.response else "No response from server"
            raise Exception(f"Amadeus API POST request to {endpoint} failed: {e}. Details: {error_details}")

    def search_flights(self,
                      origin: str,
                      destination: str,
                      departure_date: str,
                      return_date: Optional[str] = None,
                      adults: int = 1,
                      children: int = 0,
                      infants: int = 0,
                      travel_class: str = "ECONOMY",
                      max_price: Optional[int] = None,
                      currency_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for flights using Amadeus API.
       
        Args:
            origin: IATA code for origin airport (e.g., 'NYC', 'LAX')
            destination: IATA code for destination airport (e.g., 'PAR', 'LHR')
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (optional for one-way)
            adults: Number of adult passengers
            children: Number of child passengers
            infants: Number of infant passengers
            travel_class: Travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
            max_price: Maximum price filter (in the specified currency)
            currency_code: Currency code (e.g., 'INR', 'USD', 'EUR'). Defaults to INR, falls back to USD.
       
        Returns:
            Dictionary containing flight search results
        """
        if not currency_code:
            currency_code = os.getenv("AMADEUS_CURRENCY", "INR")
       
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "children": children,
            "infants": infants,
            "travelClass": travel_class,
            "currencyCode": currency_code.upper(),
            "max": 10
        }

        if return_date:
            params["returnDate"] = return_date

        if max_price:
            params["maxPrice"] = max_price

        return self._make_request("/v2/shopping/flight-offers", params)
   
    def get_flight_offers(self,
                         origin: str,
                         destination: str,
                         departure_date: str,
                         return_date: Optional[str] = None,
                         adults: int = 1,
                         currency_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Get flight offers with pricing and booking details.
       
        Args:
            origin: IATA code for origin airport
            destination: IATA code for destination airport
            departure_date: Departure date in YYYY-MM-DD format
            return_date: Return date in YYYY-MM-DD format (optional)
            adults: Number of adult passengers
            currency_code: Currency code (e.g., 'INR', 'USD', 'EUR'). Defaults to INR, falls back to USD.
        """
        if not currency_code:
            currency_code = os.getenv("AMADEUS_CURRENCY", "INR")
       
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "currencyCode": currency_code.upper()
        }
       
        if return_date:
            params["returnDate"] = return_date
       
        return self._make_request("/v2/shopping/flight-offers", params)
   
    def get_airport_city_code(self, query: str) -> str:
        """
        Get IATA code for a city name.
        """
        params = {"keyword": query, "subType": "AIRPORT,CITY"}
        result = self._make_request("/v1/reference-data/locations", params)

        if result and result.get("data"):
            return result["data"][0]["iataCode"]
        return query

    def check_flight_availability(self,
                                  origin: str,
                                  destination: str,
                                  departure_date: str,
                                  departure_time: Optional[str] = None,
                                  travelers: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Check flight seat availability using Amadeus Flight Availabilities API.
        
        Args:
            origin: IATA code for origin airport
            destination: IATA code for destination airport
            departure_date: Departure date in YYYY-MM-DD format
            departure_time: Departure time in HH:MM:SS format (optional)
            travelers: List of traveler dictionaries with 'id' and 'travelerType' 
                      (e.g., [{"id": "1", "travelerType": "ADULT"}])
        
        Returns:
            Dictionary containing flight availability information
        """
        if travelers is None:
            travelers = [{"id": "1", "travelerType": "ADULT"}]
        
        departure_datetime = {"date": departure_date}
        if departure_time:
            departure_datetime["time"] = departure_time
        
        payload = {
            "originDestinations": [
                {
                    "id": "1",
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDateTime": departure_datetime
                }
            ],
            "travelers": travelers,
            "sources": ["GDS"]
        }
        
        return self._make_post_request("/v1/shopping/availability/flight-availabilities", payload)

    def get_nearest_airports(self,
                           latitude: float,
                           longitude: float,
                           radius: int = 500,
                           page_limit: int = 10,
                           page_offset: int = 0,
                           sort: str = "relevance") -> Dict[str, Any]:
        """
        Get nearest airports to a given geographic location.
        
        Args:
            latitude: Latitude of the location (e.g., 51.57285)
            longitude: Longitude of the location (e.g., -0.44161)
            radius: Search radius in kilometers (0-500, default 500)
            page_limit: Maximum items per page (default 10)
            page_offset: Start index for pagination (default 0)
            sort: Sort order - 'relevance', 'distance', 'analytics.flights.score', 
                  or 'analytics.travelers.score' (default 'relevance')
        
        Returns:
            Dictionary containing list of nearby airports
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
            "page[limit]": page_limit,
            "page[offset]": page_offset,
            "sort": sort
        }
        
        return self._make_request("/v1/reference-data/locations/airports", params)

    def confirm_flight_pricing(self,
                              flight_offers: List[Dict[str, Any]],
                              include_options: Optional[List[str]] = None,
                              force_class: bool = False) -> Dict[str, Any]:
        """
        Confirm pricing for given flight offers.
        
        Args:
            flight_offers: List of flight offer dictionaries to confirm pricing for
            include_options: Optional list of additional info to include:
                           ['credit-card-fees', 'bags', 'other-services', 'detailed-fare-rules']
            force_class: Force usage of booking class for pricing (default False)
        
        Returns:
            Dictionary containing confirmed pricing information
        """
        payload = {
            "data": {
                "type": "flight-offers-pricing",
                "flightOffers": flight_offers
            }
        }
        
        params = {}
        if include_options:
            params["include"] = ",".join(include_options)
        if force_class:
            params["forceClass"] = "true"
        
        endpoint = "/v1/shopping/flight-offers/pricing"
        if params:
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            endpoint = f"{endpoint}?{query_string}"
        
        return self._make_post_request(endpoint, payload)


# --- Agent-Callable Tools ---

# Initialize the service as a singleton
amadeus_flights_service = AmadeusFlightsService()


def search_flights_tool(origin: str, destination: str, departure_date: str,
                       tool_context: ToolContext, return_date: Optional[str] = None,
                       adults: int = 1, travel_class: str = "ECONOMY",
                       max_price: Optional[int] = None, currency_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Searches for one-way or round-trip flight offers. Use this to find available
    flights with pricing based on origin, destination, dates, and other preferences.

    Args:
        origin: Origin airport/city code
        destination: Destination airport/city code  
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD) - optional
        adults: Number of adult passengers
        travel_class: Travel class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
        max_price: Maximum price (in the specified currency)
        currency_code: Currency code (e.g., 'INR', 'USD', 'EUR'). Defaults to INR.
        tool_context: ADK tool context
   
    Returns:
        A dictionary containing flight offer data from the Amadeus API, or an
        error dictionary if the search fails.
    """
    try:
        origin_code = amadeus_flights_service.get_airport_city_code(origin) if len(origin) > 3 else origin
        destination_code = amadeus_flights_service.get_airport_city_code(destination) if len(destination) > 3 else destination

        results = amadeus_flights_service.search_flights(
            origin=origin_code,
            destination=destination_code,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            travel_class=travel_class,
            max_price=max_price,
            currency_code=currency_code
        )
       
        if "flight_search_results" not in tool_context.state:
            tool_context.state["flight_search_results"] = []
       
        tool_context.state["flight_search_results"].append({
            "search_params": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": adults,
                "travel_class": travel_class,
                "max_price": max_price
            },
            "results": results
        })
       
        return results
       
    except Exception as e:
        return {"error": f"Flight search failed: {str(e)}"}


def get_flight_offers_tool(origin: str, destination: str, departure_date: str,
                          tool_context: ToolContext, return_date: Optional[str] = None,
                          adults: int = 1, currency_code: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool for getting detailed flight offers with pricing.
   
    Args:
        origin: Origin airport/city code
        destination: Destination airport/city code
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Return date (YYYY-MM-DD) - optional
        adults: Number of adult passengers
        currency_code: Currency code (e.g., 'INR', 'USD', 'EUR'). Defaults to INR.
        tool_context: ADK tool context
   
    Returns:
        Flight offers with pricing
    """
    try:
        results = amadeus_flights_service.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            currency_code=currency_code
        )
        return results

    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to get flight offers: {str(e)}"
        }


def check_flight_availability_tool(origin: str, destination: str, departure_date: str,
                                  tool_context: ToolContext, departure_time: Optional[str] = None,
                                  num_adults: int = 1, num_children: int = 0,
                                  num_infants: int = 0) -> Dict[str, Any]:
    """
    Check seat availability for flights on a specific route and date.
    Use this to verify if seats are available before booking.
    
    Args:
        origin: Origin airport IATA code (e.g., 'BOS', 'JFK')
        destination: Destination airport IATA code (e.g., 'MAD', 'LAX')
        departure_date: Departure date in YYYY-MM-DD format
        departure_time: Departure time in HH:MM:SS format (optional, e.g., '21:15:00')
        num_adults: Number of adult travelers (default 1)
        num_children: Number of child travelers (default 0)
        num_infants: Number of infant travelers (default 0)
        tool_context: ADK tool context
    
    Returns:
        Dictionary containing flight availability information including available seats
    """
    try:
        travelers = []
        traveler_id = 1
        
        for _ in range(num_adults):
            travelers.append({"id": str(traveler_id), "travelerType": "ADULT"})
            traveler_id += 1
        
        for _ in range(num_children):
            travelers.append({"id": str(traveler_id), "travelerType": "CHILD"})
            traveler_id += 1
        
        for _ in range(num_infants):
            travelers.append({"id": str(traveler_id), "travelerType": "HELD_INFANT"})
            traveler_id += 1
        
        results = amadeus_flights_service.check_flight_availability(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            departure_time=departure_time,
            travelers=travelers
        )
        
        if "flight_availability_results" not in tool_context.state:
            tool_context.state["flight_availability_results"] = []
        
        tool_context.state["flight_availability_results"].append({
            "search_params": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "departure_time": departure_time,
                "travelers": travelers
            },
            "results": results
        })
        
        return results
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to check flight availability: {str(e)}"
        }


def get_nearest_airports_tool(location: str,
                             tool_context: ToolContext, radius: int = 500,
                             max_results: int = 10, sort_by: str = "relevance") -> Dict[str, Any]:
    """
    Find airports near a geographic location. Use this to discover nearby airports
    when planning trips or finding alternative departure/arrival points.
    
    Args:
        latitude: Latitude coordinate (e.g., 51.57285 for London)
        longitude: Longitude coordinate (e.g., -0.44161 for London)
        radius: Search radius in kilometers, 0-500 (default 500)
        max_results: Maximum number of airports to return (default 10)
        sort_by: Sort method - 'relevance', 'distance', 'analytics.flights.score',
                or 'analytics.travelers.score' (default 'relevance')
        tool_context: ADK tool context
    
    Returns:
        Dictionary containing list of nearby airports with their details
    """
    try:
        from map_tools import get_geocode
        geo_result = get_geocode(location)
        lat = geo_result['geometry']['location']['lat']
        lng = geo_result['geometry']['location']['lng']
        valid_sort_options = ["relevance", "distance", "analytics.flights.score", "analytics.travelers.score"]
        if sort_by not in valid_sort_options:
            sort_by = "relevance"
        
        
        if not 0 <= radius <= 500:
            radius = 500
        
        results = amadeus_flights_service.get_nearest_airports(
            latitude=lat,
            longitude=lng,
            radius=radius,
            page_limit=max_results,
            sort=sort_by
        )
        
        if "nearest_airports_results" not in tool_context.state:
            tool_context.state["nearest_airports_results"] = []
        
        tool_context.state["nearest_airports_results"].append({
            "search_params": {
                "latitude": lat,
                "longitude": lng,
                "radius": radius,
                "max_results": max_results,
                "sort_by": sort_by
            },
            "results": results
        })
        
        return results
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to get nearest airports: {str(e)}"
        }


def confirm_flight_pricing_tool(flight_offer_id: str, tool_context: ToolContext,
                               include_credit_card_fees: bool = False,
                               include_bags: bool = False,
                               include_other_services: bool = False,
                               include_detailed_fare_rules: bool = False,
                               force_booking_class: bool = False) -> Dict[str, Any]:
    """
    Confirm and validate pricing for a specific flight offer before booking.
    Use this to get the final price with all fees and verify availability.
    
    Args:
        flight_offer_id: The ID of the flight offer to price (from search results)
        include_credit_card_fees: Include credit card fee information (default False)
        include_bags: Include extra baggage options (default False)
        include_other_services: Include other service options (default False)
        include_detailed_fare_rules: Include detailed fare rules (default False)
        force_booking_class: Force pricing with specified booking class (default False)
        tool_context: ADK tool context
    
    Returns:
        Dictionary containing confirmed pricing details including total cost and fees
    """
    try:
        # Retrieve the flight offer from context
        if "flight_search_results" not in tool_context.state:
            return {
                "error": True,
                "message": "No flight search results found. Please search for flights first."
            }
        
        flight_offer = None
        for search_result in tool_context.state["flight_search_results"]:
            if "results" in search_result and "data" in search_result["results"]:
                for offer in search_result["results"]["data"]:
                    if offer.get("id") == flight_offer_id:
                        flight_offer = offer
                        break
            if flight_offer:
                break
        
        if not flight_offer:
            return {
                "error": True,
                "message": f"Flight offer with ID '{flight_offer_id}' not found in search results."
            }
        
        include_options = []
        if include_credit_card_fees:
            include_options.append("credit-card-fees")
        if include_bags:
            include_options.append("bags")
        if include_other_services:
            include_options.append("other-services")
        if include_detailed_fare_rules:
            include_options.append("detailed-fare-rules")
        
        results = amadeus_flights_service.confirm_flight_pricing(
            flight_offers=[flight_offer],
            include_options=include_options if include_options else None,
            force_class=force_booking_class
        )
        
        if "pricing_confirmations" not in tool_context.state:
            tool_context.state["pricing_confirmations"] = []
        
        tool_context.state["pricing_confirmations"].append({
            "flight_offer_id": flight_offer_id,
            "include_options": include_options,
            "results": results
        })
        
        return results
        
    except Exception as e:
        return {
            "error": True,
            "message": f"Failed to confirm flight pricing: {str(e)}"
        }