
class BidirectionalLink:
    """Wrapper around two Link instances for links between two Node instances
       (from_link for a link from from_node to to_node and the opposite for to_link).
       One BidirectionalLink instance corresponds directly to one cell in the
       web interface's data table."""

    def __init__( self, from_node, to_node, from_link, to_link ):
        self.from_node = from_node
        self.to_node = to_node
        self.from_link = from_link
        self.to_link = to_link

