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

"""Asset group mutation tools for Google Ads API (PMax campaigns)."""

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools._ads_api import enum_types
from ads_mcp.tools._ads_api import resource_types
from ads_mcp.tools._ads_api import service_types
from ads_mcp.tools.mutations.common import _get_client
from ads_mcp.tools.mutations.common import _handle_google_ads_error
from ads_mcp.tools.mutations.common import _resolve_enum
from google.ads.googleads.errors import GoogleAdsException


@mcp.tool()
def create_asset_group(
    customer_id: str,
    campaign_resource_name: str,
    name: str,
    final_urls: list[str],
    status: str = "ENABLED",
    path1: str | None = None,
    path2: str | None = None,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Creates a new asset group within an existing Performance Max campaign.

  Asset groups are the creative containers for PMax campaigns. Each asset group
  holds headlines, descriptions, images, videos, and other assets that Google
  uses to auto-assemble ads across channels.

  Args:
      customer_id: Google Ads customer ID (digits only, no dashes).
      campaign_resource_name: Full resource name of the PMax campaign, e.g.
          "customers/7682222174/campaigns/22041664069".
      name: Asset group display name (e.g. "Summer Sale - Beach").
      final_urls: List of landing page URLs. At least one is required. The
          first URL is the primary destination.
      status: ENABLED or PAUSED. Defaults to ENABLED.
      path1: Optional first URL path component shown in display URL (max 15
          chars), e.g. "shop".
      path2: Optional second URL path component (max 15 chars, requires
          path1), e.g. "sale".
      login_customer_id: MCC account ID if the customer is managed.

  Returns:
      Dict with the new asset group's resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("AssetGroupService")

  asset_group = resource_types.AssetGroup(
      name=name,
      campaign=campaign_resource_name,
      status=_resolve_enum(
          enum_types.AssetGroupStatusEnum.AssetGroupStatus, status, "status"
      ),
      final_urls=final_urls,
  )
  if path1 is not None:
    asset_group.path1 = path1
  if path2 is not None:
    asset_group.path2 = path2

  operation = service_types.AssetGroupOperation(create=asset_group)
  try:
    response = service.mutate_asset_groups(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def link_asset_to_asset_group(
    customer_id: str,
    asset_group_resource_name: str,
    asset_resource_name: str,
    field_type: str,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Links an existing asset to an asset group by field type.

  Use list_account_assets to find asset resource names, and list asset groups
  via execute_gaql (SELECT asset_group.resource_name FROM asset_group).

  Supported field_type values for PMax:
    HEADLINE, LONG_HEADLINE, DESCRIPTION, LONG_DESCRIPTION,
    BUSINESS_NAME, MARKETING_IMAGE, SQUARE_MARKETING_IMAGE,
    PORTRAIT_MARKETING_IMAGE, TALL_PORTRAIT_MARKETING_IMAGE,
    LOGO, LANDSCAPE_LOGO, VIDEO, YOUTUBE_VIDEO, CALL_TO_ACTION_SELECTION,
    SITELINK, CALLOUT, STRUCTURED_SNIPPET.

  Args:
      customer_id: Google Ads customer ID (digits only, no dashes).
      asset_group_resource_name: Full resource name of the asset group, e.g.
          "customers/7682222174/assetGroups/6540223085".
      asset_resource_name: Full resource name of the asset to link, e.g.
          "customers/7682222174/assets/190051364684".
      field_type: The role this asset plays in the asset group. See the
          supported values listed above.
      login_customer_id: MCC account ID if the customer is managed.

  Returns:
      Dict with the new asset_group_asset resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("AssetGroupAssetService")

  asset_group_asset = resource_types.AssetGroupAsset(
      asset_group=asset_group_resource_name,
      asset=asset_resource_name,
      field_type=_resolve_enum(
          enum_types.AssetFieldTypeEnum.AssetFieldType, field_type, "field_type"
      ),
  )

  operation = service_types.AssetGroupAssetOperation(create=asset_group_asset)
  try:
    response = service.mutate_asset_group_assets(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_name": response.results[0].resource_name}
