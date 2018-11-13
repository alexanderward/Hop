

def success(data, paginator, page, current_page, extras=None):
	results = dict(pages=dict(total_pages=paginator.total_pages, current_page=current_page,
	                          next_page=page.next_page_number if page.has_next() else None,
	                          prev_page=page.previous_page_number if page.has_previous() else None,
	                          page_size=paginator.per_page_limit,
	                          starting_record=page.start_index,
	                          ending_record=page.end_index, total_records=paginator.count),
	               results=data)
	if extras:
		assert isinstance(extras, dict)
		results.update(extras)
	return results
