# Dropship Import MCP — Skill Guide

## When to Use This Skill

Use this MCP when a user wants to:

- Import a product from a supplier URL (AliExpress, Accio, etc.) into their online store
- Preview and edit product details before pushing to a store
- Push a prepared product to a connected store (Shopify, etc.)
- Check the status of a product push job
- Understand available pricing rules, content rules, or push options

## Workflow Overview

The import flow follows a **prepare → preview → confirm** pattern:

1. **Discover capabilities** — call `get_rule_capabilities` to see available stores, rule families, and push options.
2. **Prepare a candidate** — call `prepare_import_candidate` with a source URL, optional rules, and target store. This returns a preview bundle with a `job_id`.
3. **Review the preview** — call `get_import_preview` to inspect the prepared draft (title, images, variants, pricing).
4. **Adjust visibility** — optionally call `set_product_visibility` to switch between `backend_only` and `sell_immediately`.
5. **Push to store** — call `confirm_push_to_store` with the `job_id` and optional `push_options`.
6. **Check status** — call `get_job_status` to verify whether the push completed.

## Tool Reference

### get_rule_capabilities

Returns the provider's supported stores, rule families, and push options.

```
{ "target_store": "optional store name or ref" }
```

### validate_rules

Validates a rule object before preparing a candidate. Use this to check rules without starting the full import.

```
{
  "target_store": "optional",
  "rules": {
    "pricing": { "markup_percent": 50 },
    "content": { "title_prefix": "HOT - " },
    "images": { "max_images": 10 }
  }
}
```

### prepare_import_candidate

Resolves a source URL, imports the product, applies rules, and saves a preview bundle.

```
{
  "source_url": "https://www.aliexpress.com/item/123456.html",
  "country": "US",
  "target_store": "my-store",
  "visibility_mode": "backend_only",
  "rules": { "pricing": { "markup_percent": 30 } }
}
```

Returns a preview with `job_id`, title/image/variant diffs, and warnings.

### get_import_preview

Reload a previously prepared preview by `job_id`.

### set_product_visibility

Change the visibility mode of a prepared job before confirmation.

```
{ "job_id": "...", "visibility_mode": "sell_immediately" }
```

### confirm_push_to_store

Push the prepared draft to the target store.

```
{
  "job_id": "...",
  "push_options": {
    "publish_to_online_store": true,
    "image_strategy": "all_available",
    "pricing_rule_behavior": "keep_manual",
    "auto_inventory_update": true,
    "auto_price_update": false,
    "store_shipping_profile": [
      {
        "storeId": "...",
        "locationId": "gid://shopify/DeliveryLocationGroup/...",
        "profileId": "gid://shopify/DeliveryProfile/..."
      }
    ]
  }
}
```

### get_job_status

Returns the current status of a job (preview_ready, push_requested, completed, failed).

## Push Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `publish_to_online_store` | boolean | false | Make the product visible on the online storefront |
| `image_strategy` | string | `selected_only` | `selected_only` or `all_available` |
| `pricing_rule_behavior` | string | `keep_manual` | `keep_manual` or `apply_store_pricing_rule` |
| `auto_inventory_update` | boolean | false | Sync inventory automatically |
| `auto_price_update` | boolean | false | Sync price automatically |
| `sales_channels` | string[] | [] | Sales channel identifiers |
| `store_shipping_profile` | object[] | null | Platform delivery profile bindings (storeId, locationId, profileId) |

## Rules

Rules are applied during `prepare_import_candidate` and frozen into the job state.

- **pricing** — `markup_percent`, `fixed_markup`, `compare_at_percent`
- **content** — `title_prefix`, `title_suffix`, `title_replace`, `description_mode`
- **images** — `max_images`, `skip_first`
- **instruction_text** — free-form text instructions for the AI agent

## Error Handling

- If `prepare_import_candidate` fails, check the source URL format and country code.
- If `confirm_push_to_store` fails with a shipping profile error, provide `store_shipping_profile` in `push_options`.
- All responses include a `warnings` array — always surface these to the user.
- A job must be in `preview_ready` status before it can be confirmed.
