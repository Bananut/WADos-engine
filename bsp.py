from settings import *

class BSP:
    SUB_SECTOR_IDENTIFIER = 0x8000 # 2**15 = 32768

    def __init__(self, engine):
        self.engine = engine
        self.player = engine.player
        self.nodes = engine.wad_data.nodes
        self.sub_sectors = engine.wad_data.sub_sectors
        self.segs = engine.wad_data.segments
        self.root_node_id = len(self.nodes) - 1
    
    def update(self):
        self.render_bsp_node(node_id=self.root_node_id)

    def render_sub_sector(self, sub_sector_id):
        sub_sector = self.sub_sectors[sub_sector_id]

        for i in range(sub_sector.seg_count):
            seg = self.segs[sub_sector.first_seg_id + i]
            self.engine.map_renderer.draw_seg(seg, sub_sector_id)

    @staticmethod
    def norm(angle):
        return angle % 360

    def check_bbox(self, bbox):
        a, b = vec2(bbox.left, bbox.bottom), vec2(bbox.left, bbox.top)
        c, d = vec2(bbox.right, bbox.top), vec2(bbox.right, bbox.bottom)

        px, py = self.player.pos
        if px < bbox.left:
            if py > bbox.top:
                bbox_sides = (b, a), (c, b)
            elif py < bbox.bottom:
                bbox_sides = (b, a), (a, d)
            else:
                bbox_sides = (b, a),
        elif px > bbox.right:
            if py > bbox.top:
                bbox_sides = (c, b), (d, c)
            elif py < bbox.bottom:
                bbox_sides = (a, d), (d, c)
            else:
                bbox_sides = (d, c),
        else:
            if py > bbox.top:
                bbox_sides = (c, b),
            elif py < bbox.bottom:
                bbox_sides = (a, d),
            else:
                return True
        
        for v1, v2 in bbox_sides:
            angle1 = self.point_to_angle(v1)
            angle2 = self.point_to_angle(v2)

            span = self.norm(angle1 - angle2)

            angle1 -= self.player.angle
            span1 = self.norm(angle1 + H_FOV)
            if span1 > FOV:
                if span1 >= span + FOV:
                    continue
            return True
        return False
    
    def point_to_angle(self, vertex):
        delta = vertex - self.player.pos
        return math.degrees(math.atan2(delta.y, delta.x))

    def render_bsp_node(self, node_id):
        if node_id >= self.SUB_SECTOR_IDENTIFIER:
            sub_sector_id = node_id - self.SUB_SECTOR_IDENTIFIER
            self.render_sub_sector(sub_sector_id)
            return None

        node = self.nodes[node_id]

        is_on_back = self.is_on_back_side(node)
        if is_on_back:
            self.render_bsp_node(node.back_child_id)
            if self.check_bbox(node.bbox['front']):
                self.render_bsp_node(node.front_child_id)
        else:
            self.render_bsp_node(node.front_child_id)
            if self.check_bbox(node.bbox['back']):
                self.render_bsp_node(node.back_child_id)
    
    def is_on_back_side(self, node):
        dx = self.player.pos.x - node.x_partition
        dy = self.player.pos.y - node.y_partition
        return dx * node.dy_partition - dy * node.dx_partition <= 0