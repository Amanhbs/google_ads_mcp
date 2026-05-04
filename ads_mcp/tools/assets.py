# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Asset library inspection tools for Google Ads API."""

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools._utils import get_ads_client


# Asset types defined by Google Ads API (subset most relevant for PMax + RSAs).
# Full list: https://developers.google.com/google-ads/api/reference/rpc/v24/AssetTypeEnum.AssetType
_SUPPORTED_ASSET_TYPES = {
    "IMAGE",
    "TEXT",
    "YOUTUBE_VIDEO",
    "MEDIA_BUNDLE",
    "CALLOUT",
    "STRUCTURED_SNIPPET",
    "SITELINK",
    "PROMOTION",
    "PRICE",
    "BUSINESS_NAME",
    "BUSINESS_LOGO",
    "LEAD_FORM",
    "CALL",
    "MOBILE_APP",
    "HOTEL_CALLOUT",
    "DISCOVERY_CAROUSEL_CARD",
}


def _format_asset_row(row) -> dict:
  """Extracts the meaningful fields from one asset row into a dict."""
  asset = row.asset
  asset_type = asset.type_.name  # Enum value as string (e.g. "IMAGE")

  result = {
      "resource_name": asset.resource_name,
      "id": str(asset.id),
      "name": asset.name or "",
      "type": asset_type,
  }

  # Add type-specific preview fields so users can recognize the asset.
  if asset_type == "TEXT":
    result["text"] = asset.text_asset.text
  elif asset_type == "IMAGE":
    result["image_url"] = asset.image_asset.full_size.url or ""
    result["mime_type"] = asset.image_asset.mime_type.name
    if asset.image_asset.full_size.width_pixels:
      result["dimensions"] = (
          f"{asset.image_asset.full_size.width_pixels}x"
          f"{asset.image_asset.full_size.height_pixels}"
      )
    if asset.image_asset.file_size:
      result["file_size_bytes"] = str(asset.image_asset.file_size)
  elif asset_type == "YOUTUBE_VIDEO":
    result["youtube_video_id"] = asset.youtube_video_asset.youtube_video_id
    result["youtube_title"] = asset.youtube_video_asset.youtube_video_title
  elif asset_type == "CALLOUT":
    result["callout_text"] = asset.callout_asset.callout_text
  elif asset_type == "STRUCTURED_SNIPPET":
    result["header"] = asset.structured_snippet_asset.header
    result["values"] = list(asset.structured_snippet_asset.values)
  elif asset_type == "SITELINK":
    result["link_text"] = asset.sitelink_asset.link_text
    result["description1"] = asset.sitelink_asset.description1
    result["description2"] = asset.sitelink_asset.description2
  elif asset_type == "PROMOTION":
    result["promotion_target"] = asset.promotion_asset.promotion_target

  return result


@mcp.tool()
def list_account_assets(
    customer_id: str,
    asset_type: str | None = None,
    limit: int = 200,
) -> dict:
  """Lists assets in the account's asset library.

  Used to discover existing assets (images, text, videos, sitelinks, etc.) by
  resource_name so they can be linked to asset groups in PMax campaigns or
  used in other ad operations.

  Args:
      customer_id: Google Ads customer ID (digits only, no dashes).
      asset_type: Optional filter. One of: IMAGE, TEXT, YOUTUBE_VIDEO,
          MEDIA_BUNDLE, CALLOUT, STRUCTURED_SNIPPET, SITELINK, PROMOTION,
          PRICE, BUSINESS_NAME, BUSINESS_LOGO, LEAD_FORM, CALL, MOBILE_APP,
          HOTEL_CALLOUT, DISCOVERY_CAROUSEL_CARD. If None, returns all types.
      limit: Maximum assets to return (default 200, hard cap 1000).

  Returns:
      Dict with:
        - "count": number of assets returned
        - "asset_type_filter": the type filter that was applied (or None)
        - "assets": list of asset dicts. Each contains resource_name, id,
          name, type, and type-specific preview fields (e.g. text for TEXT
          assets, image_url for IMAGE assets).
  """
  if asset_type is not None:
    asset_type = asset_type.upper()
    if asset_type not in _SUPPORTED_ASSET_TYPES:
      raise ValueError(
          f"Unsupported asset_type '{asset_type}'. Must be one of: "
          f"{sorted(_SUPPORTED_ASSET_TYPES)}"
      )

  limit = max(1, min(limit, 1000))

  ads_client = get_ads_client()
  ga_service = ads_client.get_service("GoogleAdsService")

  query = f"""
      SELECT
          asset.resource_name,
          asset.id,
          asset.name,
          asset.type,
          asset.text_asset.text,
          asset.image_asset.full_size.url,
          asset.image_asset.full_size.width_pixels,
          asset.image_asset.full_size.height_pixels,
          asset.image_asset.mime_type,
          asset.image_asset.file_size,
          asset.youtube_video_asset.youtube_video_id,
          asset.youtube_video_asset.youtube_video_title,
          asset.callout_asset.callout_text,
          asset.structured_snippet_asset.header,
          asset.structured_snippet_asset.values,
          asset.sitelink_asset.link_text,
          asset.sitelink_asset.description1,
          asset.sitelink_asset.description2,
          asset.promotion_asset.promotion_target
      FROM asset
  """

  if asset_type is not None:
    query += f"\n      WHERE asset.type = '{asset_type}'"

  query += f"\n      LIMIT {limit}"

  request = {"customer_id": customer_id, "query": query}
  response = ga_service.search(request=request)

  assets = [_format_asset_row(row) for row in response]

  return {
      "count": len(assets),
      "asset_type_filter": asset_type,
      "assets": assets,
  }
