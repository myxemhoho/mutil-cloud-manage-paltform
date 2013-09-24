import json
import falcon

from core import api
from services.common.error_handling import not_found
from services.image import image_dispatcher as disp


class SLImageV1Image(object):
    def get_image(self, image_guid):
        client = api.config['sl_client']

        matching_image = None
        mask = get_image_mask()
        for image in client['Account'].getBlockDeviceTemplateGroups(mask=mask):
            if image.get('globalIdentifier') == image_guid:
                matching_image = image
                break

        return matching_image

    def on_get(self, req, resp, image_guid):
        results = self.get_image(image_guid)

        if not results:
            return not_found(resp, 'Image could not be found')

        resp.status = falcon.HTTP_200
        resp.body = json.dumps({'image': get_image_details_dict(results)})

    def on_head(self, req, resp, image_guid):
        results = self.get_image(image_guid)

        if not results:
            return not_found(resp, 'Image could not be found')

        headers = {
            'x-image-meta-id': image_guid,
            'x-image-meta-status': results['status'].lower(),
            'x-image-meta-owner': 'Need tenant ID here',
            'x-image-meta-name': results['name'],
            'x-image-meta-container_format': results['container_format'],
            'x-image-meta-created_at': results['created'],
            'x-image-meta-min_ram': results['minRam'],
            'x-image-meta-updated_at': results['updated'],
            'location': disp.get_endpoint_url('v1_image',
                                              image_guid=image_guid),
            'x-image-meta-deleted': False,
            'x-image-meta-protected': results['protected'],
            'x-image-meta-min_disk': results['minDisk'],
            'x-image-meta-size': results['size'],
            'x-image-meta-is_public': results['is_public'],
            'x-image-meta-disk_format': results['disk_format'],
        }

        resp.status = falcon.HTTP_200
        resp.headers = headers
        resp.body = json.dumps({'image': get_image_details_dict(results)})


class SLImageV1Images(object):
    def on_get(self, req, resp):
        client = api.config['sl_client']

        # filter = {
        #     'blockDeviceTemplateGroups':
        #     {
        #         'parentId': {
        #             'operation': 'is_null',
        #         }
        #     }
        # }
        results = []

        params = {}
        params['mask'] = get_image_mask()

        # TODO - Figure out why this filter doesn't work
#        for image in image_obj.getPublicImages():
#        images = client['Account'].getBlockDeviceTemplateGroups(filter=filter)
#        print "COUNT: " + str(len(images))
        for image in client['Account'].getBlockDeviceTemplateGroups(**params):
            if not image or image['parentId']:
                continue
            results.append(get_image_details_dict(image))

        resp.body = json.dumps({'images':
                                sorted(results,
                                       key=lambda x: x['name'].lower())})


def get_image_details_dict(image, tenant_id=None):
    if not image:
        return {}

    # TODO - Don't hardcode some of these values
    results = {
        'status': 'ACTIVE',
        'updated': image['createDate'],
        'created': image['createDate'],
        'id': image['globalIdentifier'],
        'minDisk': 0,
        'progress': 100,
        'minRam': 0,
        'metaData': None,
        'size': image.get('blockDevicesDiskSpaceTotal', 0),
        'OS-EXT-IMG-SIZE:size': None,
        'container_format': 'raw',
        'disk_format': 'raw',
        'is_public': False,
        'protected': False,
        'owner': tenant_id,
        'name': image['name'],
        'links': [
            {
                'href': disp.get_endpoint_url('v1_image',
                                              image_guid=image['id']),
                'rel': 'self',
            },
            {
                'href': disp.get_endpoint_url('v1_image',
                                              image_guid=image['id']),
                'rel': 'bookmark',
            }
        ],
        'properties': {

        },
    }

    return results


def get_image_mask():
    mask = [
        'blockDevicesDiskSpaceTotal',
        'globalIdentifier',
    ]

    return 'mask[%s]' % ','.join(mask)