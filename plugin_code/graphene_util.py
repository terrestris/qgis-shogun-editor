# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisShogunEditor
                              -------------------
        begin                : 2025-09
        git sha              : $Format:%H$
        copyright            : (C) 2025 by terrestris
        email                : info@terrestris.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import graphene
import requests


class ApplicationType(graphene.ObjectType):
    id = graphene.ID()
    name = graphene.String()
    description = graphene.String()
    layerTree = graphene.JSONString()

class Query(graphene.ObjectType):
    applications = graphene.List(ApplicationType)

    def resolve_applications(self, info):
        # You may want to parameterize the endpoint URL, here it's hardcoded for demo purposes
        shogun_url = info.context.get('shogun_url', '')
        if not shogun_url:
            return []

        # Build the applications URL (same logic as check_url_for_applications)
        if shogun_url.endswith('applications'):
            applications_url = shogun_url
        elif shogun_url.endswith('application'):
            applications_url = shogun_url + 's'
        elif shogun_url.endswith('/'):
            applications_url = shogun_url + 'applications'
        else:
            applications_url = shogun_url + '/applications'

        # Use requests to fetch (or replace with QGIS networking if needed)
        try:
            response = requests.get(applications_url, verify=False) # TODO: ssl verification handling
            if response.status_code == 200:
                applications_json = response.json()
                content = applications_json.get('content', [])
                return [
                    ApplicationType(
                        id=app.get('id'),
                        name=app.get('name'),
                        description=app.get('description'),
                        layerTree=app.get('layerTree')
                    )
                    for app in content
                ]
        except Exception as e:
            print(f"Error fetching applications: {e}")
        return []

schema = graphene.Schema(query=Query)
