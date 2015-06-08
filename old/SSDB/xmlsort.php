<?php 

	function array_sort_by_column(&$array, $column, $direction = SORT_ASC) {
	    $reference_array = array();
	    foreach($array as $key => $row) {
	        $reference_array[$key] = $row[$column];
	    }
	    array_multisort($reference_array, $direction, $array);
	}	
	
	function getXMLfromURL(){
		$xml = simplexml_load_file("https://savannah.cern.ch/export/cmscompinfrasup/gutsche/526.xml");
		//$xml = simplexml_load_file("526.xml");
		foreach($xml->item as $value){
			if(!$value->history){
				$tickets[] = array(
					'item_id' => (string)$value->item_id,
					'priority' => (string)$value->priority,
					'site' => (string)$value->custom_select_box_1,
					'open_closed' => (string)$value->open_closed,
					'submitted_on' => date('Y-m-d' ,intval($value->submitted_on)),
					'submitted_by' => (string)$value->submitted_by,
					'category' => (string)$value->category,
					'summary' => (string)$value->summary,
					'assigned_to' => (string)$value->assigned_to,
					'status' => (string)$value->status,
					'ggus'=> (string)$value->custom_text_field_1,
					'original_submission' => (string)$value->original_submission,
					'modified_by' => '',
					'modified_on' => '',
					'old_value' => ''
				);
			}else{
				$itemID = count($value->history->event) - 1; 
				$tickets[] = array(
					'item_id' => (string)$value->item_id,
					'priority' => (string)$value->priority,
					'site' => (string)$value->custom_select_box_1,
					'open_closed' => (string)$value->open_closed,
					'submitted_on' => date('Y-m-d' ,intval($value->submitted_on)),
					'submitted_by' => (string)$value->submitted_by,
					'category' => (string)$value->category,					
					'summary' => (string)$value->summary,
					'assigned_to' => (string)$value->assigned_to,
					'status' => (string)$value->status,
					'ggus'=> (string)$value->custom_text_field_1,
					'original_submission' => (string)$value->original_submission,
					'modified_by' => (string)$value->history->event[$itemID]->field->modified_by,
					'modified_on' => date('Y-m-d', intval($value->history->event[$itemID]->date)),
					'old_value' => (string)$value->history->event[$itemID]->field->old_value
				);
			} // if item has history or doesn't
		} //foreach
		return $tickets;
	} // function getXMLfromURL

?>